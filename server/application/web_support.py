import json
import os
from functools import wraps
from pathlib import Path

from django.contrib.auth.hashers import check_password, make_password
from django.db import connection
from django.db.utils import OperationalError, ProgrammingError
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import redirect

from server.domains.admin import AdminRepository
from server.domains.admin.models import SuperAdminAccount, UserAccount, Team
from server.domains.data_updates import DataUpdateRepository
from server.domains.projects import ProjectRepository, ProjectService
from server.domains.projects.models import Project
from server.domains.research_notes import ResearchNoteRepository
from server.domains.research_notes.models import ResearchNote
from server.domains.researchers import ResearcherRepository
from server.domains.signatures import SignatureRepository

admin_repository = AdminRepository()
project_repository = ProjectRepository()
researcher_repository = ResearcherRepository()
research_note_repository = ResearchNoteRepository()
data_update_repository = DataUpdateRepository()
signature_repository = SignatureRepository()
project_service = ProjectService(project_repository)
SUPER_ADMIN_JSON_PATH = Path(__file__).resolve().parent.parent / "super_admin_accounts.json"


def dashboard_counts() -> dict:
    return {
        "teams": Team.objects.count(),
        "researchers": UserAccount.objects.count(),
        "notes": ResearchNote.objects.count(),
    }

def organization_user_stats(limit: int | None = None) -> list[dict]:
    teams = Team.objects.annotate(user_count=Count("members")).order_by("-user_count", "name")
    if limit:
        teams = teams[:limit]

    stats = [
        {
            "team_id": team.id,
            "team_name": team.name,
            "user_count": team.user_count,
            "join_code": team.join_code,
        }
        for team in teams
    ]

    unassigned_count = UserAccount.objects.filter(team__isnull=True).count()
    if unassigned_count:
        stats.append(
            {
                "team_id": None,
                "team_name": "미지정",
                "user_count": unassigned_count,
                "join_code": "-",
            }
        )
    return stats


def effective_user_profile(request) -> dict | None:
    if not request.user.is_authenticated:
        return request.session.get("user_profile")

    profile = admin_repository.find_user_profile_by_username(request.user.username)
    if not profile and (request.user.is_staff or request.user.is_superuser):
        profile = admin_repository.find_super_admin_profile_by_username(request.user.username)

    if profile:
        existing = request.session.get("user_profile", {})
        if existing.get("signature_data_url"):
            profile["signature_data_url"] = existing["signature_data_url"]
        request.session["user_profile"] = profile
        return profile

    return request.session.get("user_profile")

def page_context(request, extra: dict | None = None) -> dict:
    context = {
        "current_user": effective_user_profile(request)
        or {
            "name": "게스트",
            "role": "관리자",
        }
    }
    if extra:
        context.update(extra)
    return context


def login_required_page(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user_profile = effective_user_profile(request)

        if not request.user.is_authenticated and not user_profile:
            next_url = request.get_full_path()
            return redirect(f"/login?next={next_url}")

        if (user_profile and user_profile.get("is_super_admin")) or request.user.is_staff or request.user.is_superuser:
            return redirect("/frontend/admin/dashboard")
        return view_func(request, *args, **kwargs)

    return _wrapped


def admin_required_page(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user_profile = effective_user_profile(request)
        if not user_profile and not request.user.is_authenticated:
            next_url = request.get_full_path()
            return redirect(f"/admin/login?next={next_url}")

        is_super_admin = bool((user_profile or {}).get("is_super_admin", False)) or request.user.is_staff or request.user.is_superuser
        if not is_super_admin:
            next_url = request.get_full_path()
            return redirect(f"/admin/login?next={next_url}")
        return view_func(request, *args, **kwargs)

    return _wrapped


def save_login_session(request, username: str, user: dict) -> None:
    request.session["user_profile"] = {
        "id": user.get("id"),
        "username": username,
        "name": user["name"],
        "role": user["role"],
        "email": user["email"],
        "organization": user["organization"],
        "major": user["major"],
        "team": user.get("team", "-"),
        "team_id": user.get("team_id"),
        "is_super_admin": bool(user.get("is_super_admin", False)),
        "is_approved": bool(user.get("is_approved", True)),
        "signature_data_url": request.session.get("user_profile", {}).get("signature_data_url", ""),
    }


def json_uuid_validation_error(field: str, raw_input: str) -> JsonResponse:
    return JsonResponse(
        {
            "detail": [
                {
                    "type": "uuid_parsing",
                    "loc": ["query", field],
                    "msg": "Input should be a valid UUID.",
                    "input": raw_input,
                }
            ]
        },
        status=422,
    )


def authenticate_login_user(username: str, password: str) -> dict[str, str] | None:
    return admin_repository.find_user_for_login(username, password)


def _load_super_admin_users() -> dict[str, dict[str, str]]:
    if SUPER_ADMIN_JSON_PATH.exists():
        with SUPER_ADMIN_JSON_PATH.open("r", encoding="utf-8") as file:
            payload = json.load(file)
            users = payload.get("users", {})
            if isinstance(users, dict):
                return users

    return {
        os.getenv("PROJECTNOTE_DEMO_USER", "admin"): {
            "password": os.getenv("PROJECTNOTE_DEMO_PASSWORD", "admin1234"),
            "name": os.getenv("PROJECTNOTE_DEMO_NAME", "노승희"),
            "email": os.getenv("PROJECTNOTE_DEMO_EMAIL", "paul@deep-ai.kr"),
            "organization": os.getenv("PROJECTNOTE_DEMO_ORG", "(주)딥아이"),
            "major": os.getenv("PROJECTNOTE_DEMO_MAJOR", "R&D"),
        }
    }


def _sync_super_admin_accounts() -> None:
    if not _super_admin_table_exists():
        return

    for username, user in _load_super_admin_users().items():
        try:
            raw_or_hashed_password = user.get("password", "")
            normalized_password = (
                raw_or_hashed_password
                if str(raw_or_hashed_password).startswith("pbkdf2_")
                else make_password(raw_or_hashed_password)
            )
            SuperAdminAccount.objects.update_or_create(
                username=username,
                defaults={
                    "display_name": user.get("name", username),
                    "email": user.get("email", f"{username}@projectnote.local"),
                    "password": normalized_password,
                    "organization": user.get("organization", "ProjectNote"),
                    "major": user.get("major", "관리"),
                    "is_active": True,
                },
            )
        except (OperationalError, ProgrammingError):
            return


def _super_admin_table_exists() -> bool:
    table_name = SuperAdminAccount._meta.db_table
    return table_name in connection.introspection.table_names()


def _authenticate_super_admin_from_seed_data(username: str, password: str) -> dict[str, str] | None:
    users = _load_super_admin_users()
    account = users.get(username)
    if not account:
        return None

    stored_password = account.get("password", "")
    if not (check_password(password, stored_password) or stored_password == password):
        return None

    return {
        "id": account.get("id"),
        "username": username,
        "name": account.get("name", username),
        "role": "슈퍼관리자",
        "email": account.get("email", f"{username}@projectnote.local"),
        "organization": account.get("organization", "ProjectNote"),
        "major": account.get("major", "관리"),
        "team": "SUPER_ADMIN",
        "is_super_admin": True,
    }


def authenticate_super_admin(username: str, password: str) -> dict[str, str] | None:
    if not _super_admin_table_exists():
        return _authenticate_super_admin_from_seed_data(username, password)

    _sync_super_admin_accounts()
    try:
        return admin_repository.find_super_admin_for_login(username, password)
    except (OperationalError, ProgrammingError):
        return _authenticate_super_admin_from_seed_data(username, password)
