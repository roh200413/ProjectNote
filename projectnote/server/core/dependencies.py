import json
import os
from pathlib import Path

from projectnote.workflow_app.application.services import WorkflowService
from projectnote.workflow_app.infrastructure.repositories import WorkflowRepository
from projectnote.workflow_app.models import SuperAdminAccount

repository = WorkflowRepository()
service = WorkflowService(repository)
SUPER_ADMIN_JSON_PATH = Path(__file__).resolve().parents[3] / "super_admin_accounts.json"


def load_super_admin_users() -> dict[str, dict[str, str]]:
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
    for username, user in load_super_admin_users().items():
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
