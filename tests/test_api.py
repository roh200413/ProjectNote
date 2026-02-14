import os
import uuid

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "projectnote.settings")

import django
from django.test import Client


django.setup()

client = Client()


def test_health() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_frontend_bootstrap() -> None:
    response = client.get("/api/v1/frontend/bootstrap")
    assert response.status_code == 200
    body = response.json()
    assert body["api_version"] == "v1"
    assert "api_name" in body
    assert "timestamp" in body


def test_projects_list_validation() -> None:
    response = client.get("/api/v1/projects", {"org_id": "not-a-uuid"})
    assert response.status_code == 422


def test_dashboard_summary() -> None:
    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"organizations", "projects", "notes", "revisions"}


def test_projects_list_success_without_org_id() -> None:
    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    assert response.json() == []


def test_projects_list_success_with_org_id() -> None:
    response = client.get("/api/v1/projects", {"org_id": str(uuid.uuid4())})
    assert response.status_code == 200
    assert response.json() == []
