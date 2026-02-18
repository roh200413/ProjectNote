import os
import uuid

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "projectnote.settings")

import django
from django.test import Client


django.setup()

client = Client()


def login(client_obj: Client) -> None:
    response = client_obj.post("/login", {"username": "admin", "password": "admin1234"})
    assert response.status_code == 302


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

    login(client)
    page_response = client.get("/frontend/research-notes")
    assert page_response.status_code == 200
    page_content = page_response.content.decode()
    assert "연구노트" in page_content
    assert "pn-layout" in page_content

    detail_page = client.get(f"/frontend/research-notes/{notes[0]['id']}")
    assert detail_page.status_code == 200
    assert "연구노트 다운로드" in detail_page.content.decode()


def test_workflow_pages_exist() -> None:
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
    login(client)
    projects_response = client.get("/api/v1/projects")
    project_id = projects_response.json()[0]["id"]

    project_detail = client.get(f"/frontend/projects/{project_id}")
    assert project_detail.status_code == 200
    html = project_detail.content.decode()
    assert "연구노트 업데이트" in html
    assert "집단별 연구자 목록 상세" in html

    notes_response = client.get("/api/v1/research-notes")
    note_id = notes_response.json()[0]["id"]
    viewer_response = client.get(f"/frontend/research-notes/{note_id}/viewer")
    assert viewer_response.status_code == 200
    assert "파일 정보" in viewer_response.content.decode()


def test_project_create_and_my_page_content() -> None:
    login(client)
    create_page = client.get("/frontend/projects/create")
    assert create_page.status_code == 200
    assert "프로젝트 생성" in create_page.content.decode()

    my_page = client.get("/frontend/my-page")
    assert my_page.status_code == 200
    assert "마이페이지" in my_page.content.decode()
    assert "전자서명 등록하기" in my_page.content.decode()
    assert "드래그 앤 드롭으로 이미지를 올려주세요" in my_page.content.decode()


def test_workflow_apis_support_management_actions() -> None:
    login(client)
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
            "invited_members": '[{"id":"1","role":"admin"}]',
        },
    )
    assert project_create.status_code == 201
    project_payload = project_create.json()
    assert project_payload["name"] == "신규 과제"
    assert project_payload["code"] == "TEST-001"
    assert project_payload["status"] == "active"

    detail_page = client.get(f"/frontend/projects/{project_payload['id']}")
    assert detail_page.status_code == 200
    detail_html = detail_page.content.decode()
    assert "TEST-001" in detail_html
    assert "초대 멤버" in detail_html

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
    assert researcher_create.json()["organization"] == "테스트기관"
    assert researcher_create.json()["major"] == "품질관리"

    update_create = client.post("/api/v1/data-updates", {"target": "실험로그", "status": "queued"})
    assert update_create.status_code == 201

    download_response = client.get("/api/v1/final-download")
    assert download_response.status_code == 200
    assert download_response.json()["status"] == "ready"

    sign_update = client.post("/api/v1/signatures", {"signed_by": "홍길동", "status": "valid"})
    assert sign_update.status_code == 200
    assert sign_update.json()["last_signed_by"] == "홍길동"


def test_research_note_update_api() -> None:
    login(client)
    note_id = client.get("/api/v1/research-notes").json()[0]["id"]
    response = client.post(
        f"/api/v1/research-notes/{note_id}/update",
        {"title": "업데이트 제목", "summary": "요약 수정"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["message"] == "연구노트가 업데이트되었습니다."
    assert payload["note"]["title"] == "업데이트 제목"


def test_login_logout_and_auth_redirect() -> None:
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
    assert logout["Location"] == "/login"


def test_my_page_signature_update() -> None:
    local_client = Client()
    login(local_client)

    invalid = local_client.post("/frontend/my-page/signature", {"signature_data_url": "invalid"})
    assert invalid.status_code == 400

    valid = local_client.post(
        "/frontend/my-page/signature",
        {"signature_data_url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB"},
    )
    assert valid.status_code == 200
    assert "업데이트" in valid.json()["message"]

    page = local_client.get("/frontend/my-page")
    assert page.status_code == 200
    assert "data:image/png;base64" in page.content.decode()


def test_researchers_page_separated_fields() -> None:
    local_client = Client()
    login(local_client)
    response = local_client.get("/frontend/researchers")
    assert response.status_code == 200
    html = response.content.decode()
    assert "소속/기관" in html
    assert "전공/부서명" in html
    assert "프로젝트 페이지와 겹치던 정보는 제거" in html

    projects_page = local_client.get("/frontend/projects")
    assert projects_page.status_code == 200
    assert "프로젝트 페이지는 프로젝트 정보와 상세 진입만 담당합니다." in projects_page.content.decode()
