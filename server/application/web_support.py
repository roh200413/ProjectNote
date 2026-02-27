import json
import os
from functools import wraps
from pathlib import Path

from django.db import connection
from django.db.utils import OperationalError, ProgrammingError
from django.http import JsonResponse
from django.shortcuts import redirect

from server.domains.admin import AdminRepository
from server.domains.admin.models import SuperAdminAccount, UserAccount
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
        "projects": Project.objects.count(),
        "researchers": UserAccount.objects.count(),
        "notes": ResearchNote.objects.count(),
    }


def page_context(request, extra: dict | None = None) -> dict:
    context = {
        "current_user": request.session.get(
            "user_profile",
            {
                "name": "게스트",
                "role": "관리자",
            },
        )
    }
    if extra:
        context.update(extra)
    return context


def login_required_page(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user_profile = request.session.get("user_profile")
        if not user_profile:
            next_url = request.get_full_path()
            return redirect(f"/login?next={next_url}")
        if user_profile.get("is_super_admin"):
            return redirect("/frontend/admin/dashboard")
        return view_func(request, *args, **kwargs)

    return _wrapped


def admin_required_page(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user_profile = request.session.get("user_profile")
        if not user_profile or not user_profile.get("is_super_admin"):
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
            SuperAdminAccount.objects.update_or_create(
                username=username,
                defaults={
                    "display_name": user.get("name", username),
                    "email": user.get("email", f"{username}@projectnote.local"),
                    "password": user.get("password", ""),
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
    if not account or account.get("password", "") != password:
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
