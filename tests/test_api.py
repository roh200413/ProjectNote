import os
import uuid

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "projectnote.settings")

import django
import pytest
from django.core.management import call_command
from django.test import Client


django.setup()

from projectnote.workflow_app.application.schemas import CreateProjectPayload
from projectnote.workflow_app.infrastructure.sqlalchemy_session import sqlalchemy_database_url
from projectnote.workflow_app.models import Project, ProjectMember, ResearchNote, ResearchNoteFile, ResearchNoteFolder, Researcher

pytestmark = pytest.mark.django_db


client = Client()


def reset_db() -> None:
    call_command("flush", interactive=False, verbosity=0)


def login(client_obj: Client) -> None:
    response = client_obj.post("/login", {"username": "admin", "password": "admin1234"})
    assert response.status_code == 302


def seed_workflow_data() -> tuple[str, str]:
    researcher = Researcher.objects.create(
        name="테스트연구원",
        role="연구원",
        email="tester@example.com",
        organization="테스트기관",
        major="테스트전공",
    )
    project = Project.objects.create(
        name="테스트 프로젝트",
        manager="관리자",
        organization="테스트기관",
        code="TP-001",
        status="active",
    )
    ProjectMember.objects.create(project=project, researcher=researcher, role="member")
    note = ResearchNote.objects.create(
        project=project,
        title="기본 연구노트",
        owner="관리자",
        project_code="TP-001",
        period="2026.01.01 ~ 2026.12.31",
        files=1,
        members=1,
        summary="기본 노트",
    )
    ResearchNoteFile.objects.create(
        note=note,
        name="sample.pdf",
        author="관리자",
        format="pdf",
        created="2026.02.01 / 10:00 AM",
    )
    ResearchNoteFolder.objects.create(note=note, name="[TEST - DOCS]")
    return str(project.id), str(note.id)


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
    reset_db()
    response = client.get("/api/v1/projects", {"org_id": "not-a-uuid"})
    assert response.status_code == 422


def test_dashboard_summary() -> None:
    reset_db()
    seed_workflow_data()
    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["projects"] >= 1
    assert body["notes"] >= 1


def test_projects_list_success_without_org_id() -> None:
    reset_db()
    seed_workflow_data()
    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


def test_projects_list_success_with_org_id() -> None:
    reset_db()
    seed_workflow_data()
    response = client.get("/api/v1/projects", {"org_id": str(uuid.uuid4())})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_research_notes_api_and_front_pages() -> None:
    reset_db()
    _, note_id = seed_workflow_data()

    list_response = client.get("/api/v1/research-notes")
    assert list_response.status_code == 200
    notes = list_response.json()
    assert len(notes) >= 1

    detail_response = client.get(f"/api/v1/research-notes/{note_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == note_id

    login(client)
    page_response = client.get("/frontend/research-notes")
    assert page_response.status_code == 200
    assert "연구노트" in page_response.content.decode()

    detail_page = client.get(f"/frontend/research-notes/{note_id}")
    assert detail_page.status_code == 200
    assert "연구노트 다운로드" in detail_page.content.decode()


def test_workflow_pages_exist() -> None:
    reset_db()
    seed_workflow_data()
    login(client)
    pages = [
        "/frontend/workflows",
        "/frontend/admin",
        "/frontend/projects",
        "/frontend/projects/create",
        "/frontend/my-page",
        "/frontend/researchers",
        "/frontend/data-updates",
        "/frontend/final-download",
        "/frontend/signatures",
    ]
    for path in pages:
        response = client.get(path)
        assert response.status_code == 200


def test_project_detail_and_viewer_pages() -> None:
    reset_db()
    project_id, note_id = seed_workflow_data()
    login(client)

    project_detail = client.get(f"/frontend/projects/{project_id}")
    assert project_detail.status_code == 200
    html = project_detail.content.decode()
    assert "연구노트 업데이트" in html
    assert "집단별 연구자 목록 상세" in html

    viewer_response = client.get(f"/frontend/research-notes/{note_id}/viewer")
    assert viewer_response.status_code == 200
    assert "파일 정보" in viewer_response.content.decode()


def test_project_create_and_my_page_content() -> None:
    reset_db()
    seed_workflow_data()
    login(client)
    create_page = client.get("/frontend/projects/create")
    assert create_page.status_code == 200
    assert "프로젝트 생성" in create_page.content.decode()

    my_page = client.get("/frontend/my-page")
    assert my_page.status_code == 200
    assert "마이페이지" in my_page.content.decode()


def test_workflow_apis_support_management_actions() -> None:
    reset_db()
    seed_workflow_data()
    login(client)
    researcher = Researcher.objects.first()

    project_create = client.post(
        "/api/v1/project-management",
        {
            "name": "신규 과제",
            "manager": "홍길동",
            "organization": "테스트랩",
            "code": "TEST-001",
            "description": "테스트 설명",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "status": "active",
            "invited_members": f'[{{"id":"{researcher.id}","role":"admin"}}]',
        },
    )
    assert project_create.status_code == 201
    project_payload = project_create.json()
    assert project_payload["name"] == "신규 과제"
    assert project_payload["code"] == "TEST-001"

    detail_page = client.get(f"/frontend/projects/{project_payload['id']}")
    assert detail_page.status_code == 200
    detail_html = detail_page.content.decode()
    assert "TEST-001" in detail_html

    researcher_create = client.post(
        "/api/v1/researchers",
        {
            "name": "신규연구자",
            "role": "연구보조",
            "email": "new@example.com",
            "organization": "테스트기관",
            "major": "품질관리",
        },
    )
    assert researcher_create.status_code == 201

    update_create = client.post("/api/v1/data-updates", {"target": "실험로그", "status": "queued"})
    assert update_create.status_code == 201

    download_response = client.get("/api/v1/final-download")
    assert download_response.status_code == 200

    sign_update = client.post("/api/v1/signatures", {"signed_by": "홍길동", "status": "valid"})
    assert sign_update.status_code == 200


def test_research_note_update_api() -> None:
    reset_db()
    _, note_id = seed_workflow_data()
    login(client)
    response = client.post(
        f"/api/v1/research-notes/{note_id}/update",
        {"title": "업데이트 제목", "summary": "요약 수정"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["message"] == "연구노트가 업데이트되었습니다."
    assert payload["note"]["title"] == "업데이트 제목"


def test_login_logout_and_auth_redirect() -> None:
    reset_db()
    anon = Client()
    redirect_response = anon.get("/frontend/projects")
    assert redirect_response.status_code == 302
    assert redirect_response["Location"].startswith("/login")

    bad_login = anon.post("/login", {"username": "admin", "password": "wrong"})
    assert bad_login.status_code == 401

    good_login = anon.post("/login", {"username": "admin", "password": "admin1234"})
    assert good_login.status_code == 302
    assert good_login["Location"] == "/frontend/workflows"

    my_page = anon.get("/frontend/my-page")
    assert my_page.status_code == 200
    assert "노승희" in my_page.content.decode()

    logout = anon.get("/logout")
    assert logout.status_code == 302


def test_my_page_signature_update() -> None:
    reset_db()
    local_client = Client()
    login(local_client)

    invalid = local_client.post("/frontend/my-page/signature", {"signature_data_url": "invalid"})
    assert invalid.status_code == 400

    valid = local_client.post(
        "/frontend/my-page/signature",
        {"signature_data_url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB"},
    )
    assert valid.status_code == 200

    page = local_client.get("/frontend/my-page")
    assert page.status_code == 200
    assert "data:image/png;base64" in page.content.decode()


def test_researchers_page_separated_fields() -> None:
    reset_db()
    seed_workflow_data()
    local_client = Client()
    login(local_client)
    response = local_client.get("/frontend/researchers")
    assert response.status_code == 200
    html = response.content.decode()
    assert "소속/기관" in html
    assert "전공/부서명" in html

    projects_page = local_client.get("/frontend/projects")
    assert projects_page.status_code == 200
    assert "프로젝트 페이지는 프로젝트 정보와 상세 진입만 담당합니다." in projects_page.content.decode()


def test_seed_demo_command_populates_tables() -> None:
    reset_db()
    call_command("seed_demo", "--reset", verbosity=0)

    assert Project.objects.count() >= 1
    assert Researcher.objects.count() >= 2
    assert ResearchNote.objects.count() >= 1

    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_ddd_supporting_layers_are_wired() -> None:
    reset_db()

    payload = CreateProjectPayload(name="DDD 검증 프로젝트", manager="관리자")
    assert payload.name == "DDD 검증 프로젝트"
    assert payload.status == "draft"

    db_url = sqlalchemy_database_url()
    assert db_url.startswith("sqlite:///")
