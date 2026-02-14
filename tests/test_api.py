import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_projects_list_validation() -> None:
    response = client.get("/api/v1/projects", params={"org_id": "not-a-uuid"})
    assert response.status_code == 422
