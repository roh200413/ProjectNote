import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


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


def test_projects_list_validation() -> None:
    response = client.get("/api/v1/projects", params={"org_id": "not-a-uuid"})
    assert response.status_code == 422


def test_dashboard_summary() -> None:
    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"organizations", "projects", "notes", "revisions"}
