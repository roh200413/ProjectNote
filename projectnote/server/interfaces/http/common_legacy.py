import json
import os
from functools import wraps
from pathlib import Path

from django.http import JsonResponse
from django.shortcuts import redirect

from projectnote.workflow_app.application.services import WorkflowService
from projectnote.workflow_app.infrastructure.repositories import WorkflowRepository
from projectnote.workflow_app.models import SuperAdminAccount

repository = WorkflowRepository()
service = WorkflowService(repository)

SUPER_ADMIN_JSON_PATH = Path(__file__).resolve().parents[4] / "super_admin_accounts.json"


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


def save_login_session(request, username: str, user: dict[str, str]) -> None:
    request.session["user_profile"] = {
        "username": username,
        "name": user["name"],
        "role": user["role"],
        "email": user["email"],
        "organization": user["organization"],
        "major": user["major"],
        "team": user.get("team", "-"),
        "is_super_admin": bool(user.get("is_super_admin", False)),
        "signature_data_url": request.session.get("user_profile", {}).get("signature_data_url", ""),
    }


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


def sync_super_admin_accounts() -> None:
    for username, user in _load_super_admin_users().items():
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


def authenticate_login_user(username: str, password: str) -> dict[str, str] | None:
    return repository.find_user_for_login(username, password)


def authenticate_super_admin(username: str, password: str) -> dict[str, str] | None:
    sync_super_admin_accounts()
    return repository.find_super_admin_for_login(username, password)


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
