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
    assert isinstance(response.json(), list)


def test_projects_list_success_with_org_id() -> None:
    response = client.get("/api/v1/projects", {"org_id": str(uuid.uuid4())})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_research_notes_api_and_front_pages() -> None:
    list_response = client.get("/api/v1/research-notes")
    assert list_response.status_code == 200
    notes = list_response.json()
    assert len(notes) >= 1

    detail_response = client.get(f"/api/v1/research-notes/{notes[0]['id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == notes[0]["id"]

    page_response = client.get("/frontend/research-notes")
    assert page_response.status_code == 200
    assert "연구노트" in page_response.content.decode()

    detail_page = client.get(f"/frontend/research-notes/{notes[0]['id']}")
    assert detail_page.status_code == 200
    assert "연구노트 다운로드" in detail_page.content.decode()


def test_workflow_pages_exist() -> None:
    pages = [
        "/frontend/workflows",
        "/frontend/projects",
        "/frontend/researchers",
        "/frontend/data-updates",
        "/frontend/final-download",
        "/frontend/signatures",
    ]
    for path in pages:
        response = client.get(path)
        assert response.status_code == 200


def test_workflow_apis_support_management_actions() -> None:
    project_create = client.post("/api/v1/project-management", {"name": "신규 과제", "manager": "홍길동"})
    assert project_create.status_code == 201
    assert project_create.json()["name"] == "신규 과제"

    researcher_create = client.post(
        "/api/v1/researchers",
        {"name": "신규연구자", "role": "연구보조", "email": "new@example.com"},
    )
    assert researcher_create.status_code == 201

    update_create = client.post("/api/v1/data-updates", {"target": "실험로그", "status": "queued"})
    assert update_create.status_code == 201

    download_response = client.get("/api/v1/final-download")
    assert download_response.status_code == 200
    assert download_response.json()["status"] == "ready"

    sign_update = client.post("/api/v1/signatures", {"signed_by": "홍길동", "status": "valid"})
    assert sign_update.status_code == 200
    assert sign_update.json()["last_signed_by"] == "홍길동"
