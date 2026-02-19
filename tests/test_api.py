import os
import uuid

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "projectnote.settings")

import django
import pytest
from django.core.management import call_command
from django.test import Client


django.setup()

from projectnote.workflow_app.application.schemas import CreateProjectPayload
from projectnote.workflow_app.domains.projects.service import ProjectService
from projectnote.workflow_app.infrastructure.sqlalchemy_session import sqlalchemy_database_url
from projectnote.workflow_app.models import Project, ProjectMember, ResearchNote, ResearchNoteFile, ResearchNoteFolder, Researcher, Team, UserAccount

pytestmark = pytest.mark.django_db


client = Client()


def reset_db() -> None:
    call_command("flush", interactive=False, verbosity=0)


def login(client_obj: Client) -> None:
    team, _ = Team.objects.get_or_create(name="기본팀", defaults={"description": "기본", "join_code": "123456"})
    UserAccount.objects.get_or_create(
        username="member-login",
        defaults={
            "display_name": "기본사용자",
            "email": "member-login@example.com",
            "password": "admin1234",
            "role": UserAccount.Role.MEMBER,
            "team": team,
        },
    )
    response = client_obj.post("/login", {"username": "member-login", "password": "admin1234"})
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

    admin_restricted_pages = [
        "/frontend/admin/dashboard",
        "/frontend/admin/teams",
        "/frontend/admin/users",
        "/frontend/admin/tables",
    ]
    for path in admin_restricted_pages:
        response = client.get(path)
        assert response.status_code == 302
        assert response["Location"].startswith("/admin/login")


def test_admin_pages_require_admin_login() -> None:
    reset_db()
    anon = Client()

    admin_dashboard = anon.get("/frontend/admin/dashboard")
    assert admin_dashboard.status_code == 302
    assert admin_dashboard["Location"].startswith("/admin/login?next=")

    admin_login_page = anon.get("/admin/login")
    assert admin_login_page.status_code == 200
    assert "관리자 로그인" in admin_login_page.content.decode()

    bad_login = anon.post("/admin/login", {"username": "admin", "password": "wrong"})
    assert bad_login.status_code == 401

    ok_login = anon.post("/admin/login", {"username": "admin", "password": "admin1234"})
    assert ok_login.status_code == 302
    assert ok_login["Location"] == "/frontend/admin/dashboard"


def test_non_super_admin_cannot_access_admin_pages() -> None:
    reset_db()
    seed_workflow_data()
    client_obj = Client()
    signup = client_obj.post(
        "/api/v1/auth/signup",
        {
            "username": "teamadmin",
            "display_name": "팀관리자",
            "email": "teamadmin@example.com",
            "password": "secret123",
            "role": "admin",
            "team_name": "테스트팀",
            "team_description": "테스트",
        },
    )
    assert signup.status_code == 201

    login_response = client_obj.post("/login", {"username": "teamadmin", "password": "secret123"})
    assert login_response.status_code == 302
    assert login_response["Location"] == "/frontend/workflows"

    admin_page = client_obj.get("/frontend/admin/dashboard")
    assert admin_page.status_code == 302
    assert admin_page["Location"].startswith("/admin/login")


def test_super_admin_cannot_access_regular_workflow_pages() -> None:
    reset_db()
    local_client = Client()

    admin_login = local_client.post("/admin/login", {"username": "admin", "password": "admin1234"})
    assert admin_login.status_code == 302
    assert admin_login["Location"] == "/frontend/admin/dashboard"

    workflow_page = local_client.get("/frontend/workflows")
    assert workflow_page.status_code == 302
    assert workflow_page["Location"] == "/frontend/admin/dashboard"


def test_super_admin_can_manage_only_data_tables() -> None:
    reset_db()
    local_client = Client()
    local_client.post("/admin/login", {"username": "admin", "password": "admin1234"})

    dashboard = local_client.get("/frontend/admin/dashboard")
    assert dashboard.status_code == 200

    tables_page = local_client.get("/frontend/admin/tables")
    assert tables_page.status_code == 200

    teams_page = local_client.get("/frontend/admin/teams")
    assert teams_page.status_code == 403

    users_page = local_client.get("/frontend/admin/users")
    assert users_page.status_code == 403

    teams_api = local_client.get("/api/v1/admin/teams")
    assert teams_api.status_code == 403

    users_api = local_client.get("/api/v1/admin/users")
    assert users_api.status_code == 403


def test_user_without_team_is_blocked_from_home() -> None:
    reset_db()
    client_obj = Client()
    signup = client_obj.post(
        "/api/v1/auth/signup",
        {
            "username": "noteam",
            "display_name": "무소속",
            "email": "noteam@example.com",
            "password": "secret123",
            "role": "member",
        },
    )
    assert signup.status_code == 201

    login_response = client_obj.post("/login", {"username": "noteam", "password": "secret123"})
    assert login_response.status_code == 403
    assert "관리자 팀 할당 및 승인이 되지 않았습니다." in login_response.content.decode()


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

    login_page = anon.get("/login")
    assert login_page.status_code == 200
    login_html = login_page.content.decode()
    assert 'href="/signup"' in login_html
    assert "<h2>회원가입</h2>" not in login_html

    signup_page = anon.get("/signup")
    assert signup_page.status_code == 200
    assert "회원가입" in signup_page.content.decode()

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


def test_domain_oriented_project_service_exists() -> None:
    service = ProjectService()
    assert hasattr(service, "create_project")


def test_signup_and_admin_user_management_tables() -> None:
    reset_db()
    seed_workflow_data()

    admin_signup = client.post(
        "/api/v1/auth/signup",
        {
            "username": "leader",
            "display_name": "팀장",
            "email": "leader@example.com",
            "password": "secret123",
            "role": "admin",
            "team_name": "플랫폼팀",
            "team_description": "운영팀",
        },
    )
    assert admin_signup.status_code == 201
    join_code = admin_signup.json()["join_code"]
    assert len(join_code) == 6

    member_signup = client.post(
        "/api/v1/auth/signup",
        {
            "username": "member1",
            "display_name": "일반회원",
            "email": "member1@example.com",
            "password": "secret123",
            "role": "member",
            "team_name": "플랫폼팀",
            "team_code": join_code,
        },
    )
    assert member_signup.status_code == 201
    assert member_signup.json()["team"] == "플랫폼팀"

    local_client = Client()
    login(local_client)
    users = local_client.get("/api/v1/admin/users")
    assert users.status_code == 200
    users_payload = users.json()
    assert any(item["username"] == "leader" and item["role"] == "관리자" for item in users_payload)
    assert any(item["username"] == "member1" and item["role"] == "일반" for item in users_payload)

    admin_redirect = local_client.get("/frontend/admin")
    assert admin_redirect.status_code == 302
    assert admin_redirect["Location"] == "/frontend/admin/dashboard"

    admin_page = local_client.get("/frontend/admin/teams")
    assert admin_page.status_code == 200
    html = admin_page.content.decode()
    assert "팀 관리" in html

    users_page = local_client.get("/frontend/admin/users")
    assert users_page.status_code == 200
    assert "모든 가입자 관리" in users_page.content.decode()

    tables = local_client.get("/api/v1/admin/tables")
    assert tables.status_code == 200
    tables_payload = tables.json()
    assert any(item["table"] == "workflow_app_useraccount" for item in tables_payload)
