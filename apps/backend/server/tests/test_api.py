import os
import tempfile
import uuid

import pytest
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.config.settings")

import django
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import Client, override_settings


django.setup()

from server.domains.projects.schemas import CreateProjectPayload
from server.domains.projects.service import ProjectService
from server.application.sqlalchemy_session import sqlalchemy_database_url
from server.application import web_support
from server.application.mock_data import seed_demo_data
from server.domains.admin.models import Team, UserAccount
from server.domains.projects.models import Project, ProjectMember
from server.domains.research_notes.models import ResearchNote, ResearchNoteFile, ResearchNoteFolder

pytestmark = pytest.mark.django_db


client = Client()
User = get_user_model()


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
            "is_approved": True,
        },
    )
    response = client_obj.post("/login", {"username": "member-login", "password": "admin1234"})
    assert response.status_code == 302


def seed_workflow_data() -> tuple[str, str]:
    team, _ = Team.objects.get_or_create(name="테스트기관", defaults={"description": "테스트팀", "join_code": "111111"})
    user, _ = UserAccount.objects.get_or_create(
        username="tester",
        defaults={
            "display_name": "테스트연구원",
            "email": "tester@example.com",
            "password": "secret123",
            "role": UserAccount.Role.MEMBER,
            "team": team,
            "is_approved": True,
        },
    )
    project = Project.objects.create(
        name="테스트 프로젝트",
        manager="관리자",
        organization="테스트기관",
        code="TP-001",
        status="active",
    )
    ProjectMember.objects.create(project=project, user=user, role="member")
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




def test_signup_stores_hashed_password() -> None:
    reset_db()
    response = client.post(
        "/api/v1/auth/signup",
        {
            "username": "hash-user",
            "display_name": "해시유저",
            "email": "hash-user@example.com",
            "password": "secret123",
            "role": "owner",
            "team_name": "해시팀",
            "team_description": "보안",
        },
    )

    assert response.status_code == 201
    created = UserAccount.objects.get(username="hash-user")
    assert created.password != "secret123"
    assert check_password("secret123", created.password)




def test_first_approved_user_becomes_owner() -> None:
    reset_db()
    team = Team.objects.create(name="첫승인팀", description="첫승인", join_code="121212")
    user = UserAccount.objects.create(
        username="first-approve",
        display_name="첫승인유저",
        email="first-approve@example.com",
        password="secret123",
        role=UserAccount.Role.MEMBER,
        team=team,
        is_approved=False,
    )

    super_client = Client()
    assert super_client.post("/admin/login", {"username": "admin", "password": "admin1234"}).status_code == 302
    approve = super_client.post("/api/v1/admin/users", {"action": "approve", "user_id": str(user.id)})

    assert approve.status_code == 200
    user.refresh_from_db()
    assert user.is_approved is True
    assert user.role == UserAccount.Role.OWNER


def test_dashboard_can_change_team_owner() -> None:
    reset_db()
    team = Team.objects.create(name="소유주변경팀", description="변경", join_code="343434")
    old_owner = UserAccount.objects.create(
        username="old-owner",
        display_name="기존소유주",
        email="old-owner@example.com",
        password="secret123",
        role=UserAccount.Role.OWNER,
        team=team,
        is_approved=True,
    )
    new_owner = UserAccount.objects.create(
        username="new-owner",
        display_name="신규소유주",
        email="new-owner@example.com",
        password="secret123",
        role=UserAccount.Role.ADMIN,
        team=team,
        is_approved=True,
    )

    super_client = Client()
    assert super_client.post("/admin/login", {"username": "admin", "password": "admin1234"}).status_code == 302
    change = super_client.post(
        "/api/v1/admin/users",
        {
            "action": "set_owner",
            "team_id": str(team.id),
            "owner_user_id": str(new_owner.id),
        },
    )

    assert change.status_code == 200
    old_owner.refresh_from_db()
    new_owner.refresh_from_db()
    assert old_owner.role == UserAccount.Role.ADMIN
    assert new_owner.role == UserAccount.Role.OWNER

def test_owner_signup_requires_super_admin_approval_to_create_team() -> None:
    reset_db()

    signup = client.post(
        "/api/v1/auth/signup",
        {
            "username": "owner-approval",
            "display_name": "소유자승인",
            "email": "owner-approval@example.com",
            "password": "secret123",
            "role": "owner",
            "team_name": "승인생성팀",
            "team_description": "승인 후 생성",
        },
    )
    assert signup.status_code == 201
    assert not Team.objects.filter(name="승인생성팀").exists()

    super_client = Client()
    assert super_client.post("/admin/login", {"username": "admin", "password": "admin1234"}).status_code == 302
    owner_id = UserAccount.objects.get(username="owner-approval").id
    approve = super_client.post("/api/v1/admin/users", {"action": "approve", "user_id": str(owner_id)})

    assert approve.status_code == 200
    created_team = Team.objects.get(name="승인생성팀")
    owner = UserAccount.objects.get(id=owner_id)
    assert owner.team_id == created_team.id
    assert owner.is_approved is True


def test_login_supports_legacy_plaintext_password_and_upgrades_hash() -> None:
    reset_db()
    team = Team.objects.create(name="레거시팀", description="레거시", join_code="444444")
    user = UserAccount.objects.create(
        username="legacy-user",
        display_name="레거시유저",
        email="legacy-user@example.com",
        password="legacy-pass",
        role=UserAccount.Role.MEMBER,
        team=team,
        is_approved=True,
    )

    response = client.post("/login", {"username": "legacy-user", "password": "legacy-pass"})

    assert response.status_code == 302
    assert response["Location"] == "/frontend/workflows"
    user.refresh_from_db()
    assert user.password != "legacy-pass"
    assert check_password("legacy-pass", user.password)


def test_super_admin_seed_password_accepts_hashed_value(monkeypatch) -> None:
    reset_db()
    hashed = make_password("admin1234")
    monkeypatch.setattr(
        web_support,
        "_load_super_admin_users",
        lambda: {
            "admin": {
                "password": hashed,
                "name": "관리자",
                "email": "admin@example.com",
                "organization": "ProjectNote",
                "major": "관리",
            }
        },
    )
    monkeypatch.setattr(web_support, "_super_admin_table_exists", lambda: False)

    user = web_support.authenticate_super_admin("admin", "admin1234")

    assert user is not None
    assert user["is_super_admin"] is True



def test_login_sets_django_auth_session_keys() -> None:
    reset_db()
    team = Team.objects.create(name="세션팀", description="세션", join_code="555555")
    UserAccount.objects.create(
        username="session-user",
        display_name="세션유저",
        email="session-user@example.com",
        password=make_password("secret123"),
        role=UserAccount.Role.MEMBER,
        team=team,
        is_approved=True,
    )

    response = client.post("/login", {"username": "session-user", "password": "secret123"})

    assert response.status_code == 302
    assert response["Location"] == "/frontend/workflows"
    assert "_auth_user_id" in client.session
    assert "user_profile" in client.session


def test_logout_clears_django_auth_and_custom_session() -> None:
    reset_db()
    team = Team.objects.create(name="로그아웃팀", description="로그아웃", join_code="666666")
    UserAccount.objects.create(
        username="logout-user",
        display_name="로그아웃유저",
        email="logout-user@example.com",
        password=make_password("secret123"),
        role=UserAccount.Role.MEMBER,
        team=team,
        is_approved=True,
    )
    client.post("/login", {"username": "logout-user", "password": "secret123"})

    response = client.get("/logout")

    assert response.status_code == 302
    assert response["Location"] == "/login"
    assert "_auth_user_id" not in client.session
    assert "user_profile" not in client.session



def test_workflow_page_allows_django_authenticated_user_without_custom_session() -> None:
    reset_db()
    user = User.objects.create_user(username="django-only", password="secret123")
    client_obj = Client()
    client_obj.force_login(user)

    response = client_obj.get("/frontend/workflows")

    assert response.status_code == 200


def test_admin_page_allows_staff_django_user_without_custom_session() -> None:
    reset_db()
    staff = User.objects.create_user(username="django-staff", password="secret123", is_staff=True, is_superuser=True)
    client_obj = Client()
    client_obj.force_login(staff)

    response = client_obj.get("/frontend/admin/dashboard")

    assert response.status_code == 200



def test_login_does_not_set_legacy_super_admin_session_flag_for_member() -> None:
    reset_db()
    team = Team.objects.create(name="플래그팀", description="플래그", join_code="777777")
    UserAccount.objects.create(
        username="flag-user",
        display_name="플래그유저",
        email="flag-user@example.com",
        password=make_password("secret123"),
        role=UserAccount.Role.MEMBER,
        team=team,
        is_approved=True,
    )

    response = client.post("/login", {"username": "flag-user", "password": "secret123"})

    assert response.status_code == 302
    assert "pn_is_super_admin" not in client.session



def test_effective_user_profile_refreshes_session_data_after_account_change() -> None:
    reset_db()
    team = Team.objects.create(name="갱신팀", description="갱신", join_code="888888")
    user = UserAccount.objects.create(
        username="refresh-user",
        display_name="이전이름",
        email="refresh-user@example.com",
        password=make_password("secret123"),
        role=UserAccount.Role.MEMBER,
        team=team,
        is_approved=True,
    )

    client.post("/login", {"username": "refresh-user", "password": "secret123"})
    user.display_name = "변경된이름"
    user.save(update_fields=["display_name", "updated_at"])

    response = client.get("/frontend/workflows")

    assert response.status_code == 200
    assert client.session.get("user_profile", {}).get("name") == "변경된이름"


def test_researchers_api_allows_staff_user_without_custom_profile() -> None:
    reset_db()
    staff = User.objects.create_user(username="staff-manager", password="secret123", is_staff=True, is_superuser=True)
    client_obj = Client()
    client_obj.force_login(staff)

    response = client_obj.post("/api/v1/researchers", {"action": "approve", "user_id": "999"})

    assert response.status_code == 302
    assert response["Location"] == "/frontend/admin/dashboard"

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
    assert "파일 보기" in detail_page.content.decode()


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
        "/frontend/integrations/github",
        "/frontend/integrations/collaboration",
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
            "role": "owner",
            "team_name": "테스트팀",
            "team_description": "테스트",
        },
    )
    assert signup.status_code == 201

    login_response = client_obj.post("/login", {"username": "teamadmin", "password": "secret123"})
    assert login_response.status_code == 403
    assert ("관리자 승인 대기 중입니다." in login_response.content.decode() or "관리자 팀 할당 및 승인" in login_response.content.decode())

    admin_page = client_obj.get("/frontend/admin/dashboard")
    assert admin_page.status_code == 302
    assert admin_page["Location"].startswith("/admin/login")


def test_super_admin_can_manage_admin_pages_and_teams_api() -> None:
    reset_db()
    local_client = Client()
    local_client.post("/admin/login", {"username": "admin", "password": "admin1234"})

    dashboard = local_client.get("/frontend/admin/dashboard")
    assert dashboard.status_code == 200

    tables_page = local_client.get("/frontend/admin/tables")
    assert tables_page.status_code == 200

    teams_page = local_client.get("/frontend/admin/teams")
    assert teams_page.status_code == 200

    users_page = local_client.get("/frontend/admin/users")
    assert users_page.status_code == 200

    # 팀 조회 가능
    teams_api = local_client.get("/api/v1/admin/teams")
    assert teams_api.status_code == 200
    assert isinstance(teams_api.json(), list)

    # 팀 생성 가능
    create_team = local_client.post(
        "/api/v1/admin/teams",
        {"name": "슈퍼팀", "description": "슈퍼어드민이 생성"},
    )
    assert create_team.status_code == 201
    assert create_team.json()["name"] == "슈퍼팀"


def test_organization_user_stats_includes_owner_name() -> None:
    reset_db()
    team = Team.objects.create(name="대시보드팀", description="대시보드", join_code="909090")
    UserAccount.objects.create(
        username="owner-dashboard",
        display_name="대시보드소유자",
        email="owner-dashboard@example.com",
        password="secret123",
        role=UserAccount.Role.OWNER,
        team=team,
        is_approved=True,
    )

    stats = web_support.organization_user_stats()
    dashboard_team = next(item for item in stats if item["team_name"] == "대시보드팀")

    assert dashboard_team["owner_name"] == "대시보드소유자"



def test_super_admin_can_login_from_general_login_page() -> None:
    reset_db()
    local_client = Client()

    response = local_client.post("/login", {"username": "admin", "password": "admin1234"})

    assert response.status_code == 302
    assert response["Location"] == "/frontend/admin/dashboard"

    dashboard_redirect = local_client.get("/frontend/workflows")
    assert dashboard_redirect.status_code == 302
    assert dashboard_redirect["Location"] == "/frontend/admin/dashboard"


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
    assert teams_page.status_code == 200

    users_page = local_client.get("/frontend/admin/users")
    assert users_page.status_code == 200

    teams_api = local_client.get("/api/v1/admin/teams")
    assert teams_api.status_code == 200



def test_super_admin_login_falls_back_when_super_admin_table_missing(monkeypatch) -> None:
    monkeypatch.setattr(web_support, "_super_admin_table_exists", lambda: False)

    user = web_support.authenticate_super_admin("admin", "admin1234")

    assert user is not None
    assert user["username"] == "admin"
    assert user["is_super_admin"] is True




def test_project_update_api() -> None:
    reset_db()
    project_id, _ = seed_workflow_data()

    response = client.post(
        f"/api/v1/projects/{project_id}/update",
        {
            "name": "수정 프로젝트",
            "manager": "새 책임자",
            "organization": "새 기관",
            "code": "NEW-001",
            "description": "설명 수정",
            "start_date": "2026-03-01",
            "end_date": "2026-12-31",
            "status": "draft",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "수정 프로젝트"
    assert body["manager"] == "새 책임자"
    assert body["code"] == "NEW-001"


def test_project_add_researcher_api_team_only() -> None:
    reset_db()
    team = Team.objects.create(name="우리팀", description="우리팀", join_code="222222")
    other_team = Team.objects.create(name="다른팀", description="다른팀", join_code="333333")

    project = Project.objects.create(
        name="우리팀 프로젝트",
        manager="팀장",
        organization="우리팀",
        company=team,
        code="TEAM-01",
        status="active",
    )

    my_member = UserAccount.objects.create(
        username="my-member",
        display_name="우리팀연구원",
        email="my-member@example.com",
        password="secret123",
        role=UserAccount.Role.MEMBER,
        team=team,
        is_approved=True,
    )
    other_member = UserAccount.objects.create(
        username="other-member",
        display_name="다른팀연구원",
        email="other-member@example.com",
        password="secret123",
        role=UserAccount.Role.MEMBER,
        team=other_team,
        is_approved=True,
    )

    ok_response = client.post(
        f"/api/v1/projects/{project.id}/researchers",
        {"user_id": my_member.id},
    )
    assert ok_response.status_code == 200
    assert ProjectMember.objects.filter(project=project, user=my_member).exists()

    fail_response = client.post(
        f"/api/v1/projects/{project.id}/researchers",
        {"user_id": other_member.id},
    )
    assert fail_response.status_code == 400
    assert "우리팀 연구원만 추가" in fail_response.json()["detail"]


def test_project_remove_researcher_api() -> None:
    reset_db()
    team = Team.objects.create(name="우리팀", description="우리팀", join_code="232323")
    project = Project.objects.create(
        name="우리팀 프로젝트",
        manager="팀장",
        organization="우리팀",
        company=team,
        code="TEAM-02",
        status="active",
    )

    UserAccount.objects.create(
        username="project-admin",
        display_name="프로젝트관리자",
        email="project-admin@example.com",
        password="secret123",
        role=UserAccount.Role.ADMIN,
        team=team,
        is_approved=True,
    )
    member = UserAccount.objects.create(
        username="project-member",
        display_name="프로젝트멤버",
        email="project-member@example.com",
        password="secret123",
        role=UserAccount.Role.MEMBER,
        team=team,
        is_approved=True,
    )
    ProjectMember.objects.create(project=project, user=member, role="member")

    login_response = client.post("/login", {"username": "project-admin", "password": "secret123"})
    assert login_response.status_code == 302

    response = client.post(f"/api/v1/projects/{project.id}/researchers/remove", {"user_id": member.id})

    assert response.status_code == 200
    assert not ProjectMember.objects.filter(project=project, user=member).exists()


def test_member_sees_only_participating_projects_and_cannot_manage_researchers() -> None:
    reset_db()
    team = Team.objects.create(name="접근팀", description="접근팀", join_code="454545")
    member = UserAccount.objects.create(
        username="limited-member",
        display_name="참여연구원",
        email="limited-member@example.com",
        password="secret123",
        role=UserAccount.Role.MEMBER,
        team=team,
        is_approved=True,
    )
    project_joined = Project.objects.create(name="참여 프로젝트", manager="팀장", organization="접근팀", company=team, status="active")
    project_other = Project.objects.create(name="비참여 프로젝트", manager="팀장", organization="접근팀", company=team, status="active")
    ProjectMember.objects.create(project=project_joined, user=member, role="member")

    client_obj = Client()
    login_response = client_obj.post("/login", {"username": "limited-member", "password": "secret123"})
    assert login_response.status_code == 302

    projects_page = client_obj.get("/frontend/projects")
    assert projects_page.status_code == 200
    html = projects_page.content.decode()
    assert "참여 프로젝트" in html
    assert "비참여 프로젝트" not in html

    hidden_project = client_obj.get(f"/frontend/projects/{project_other.id}")
    assert hidden_project.status_code == 404

    forbidden_add = client_obj.post(f"/api/v1/projects/{project_joined.id}/researchers", {"user_id": member.id})
    assert forbidden_add.status_code == 403


def test_admin_can_view_all_project_pages() -> None:
    reset_db()
    team = Team.objects.create(name="운영팀", description="운영팀", join_code="787878")
    UserAccount.objects.create(
        username="team-admin",
        display_name="팀관리자",
        email="team-admin@example.com",
        password="secret123",
        role=UserAccount.Role.ADMIN,
        team=team,
        is_approved=True,
    )
    project = Project.objects.create(name="운영 프로젝트", manager="관리자", organization="운영팀", company=team, status="active")

    client_obj = Client()
    login_response = client_obj.post("/login", {"username": "team-admin", "password": "secret123"})
    assert login_response.status_code == 302

    assert client_obj.get("/frontend/projects").status_code == 200
    assert client_obj.get(f"/frontend/projects/{project.id}").status_code == 200
    assert client_obj.get(f"/frontend/projects/{project.id}/researchers").status_code == 200
    assert client_obj.get(f"/frontend/projects/{project.id}/research-notes").status_code == 200

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
            "role": "owner",
            "team_name": "테스트팀",
            "team_description": "테스트",
        },
    )
    assert signup.status_code == 201

    login_response = client_obj.post("/login", {"username": "teamadmin", "password": "secret123"})
    assert login_response.status_code == 403
    assert ("관리자 승인 대기 중입니다." in login_response.content.decode() or "관리자 팀 할당 및 승인" in login_response.content.decode())

    admin_page = client_obj.get("/frontend/admin/dashboard")
    assert admin_page.status_code == 302
    assert admin_page["Location"].startswith("/admin/login")




def test_project_update_api() -> None:
    reset_db()
    project_id, _ = seed_workflow_data()

    response = client.post(
        f"/api/v1/projects/{project_id}/update",
        {
            "name": "수정 프로젝트",
            "manager": "새 책임자",
            "organization": "새 기관",
            "code": "NEW-001",
            "description": "설명 수정",
            "start_date": "2026-03-01",
            "end_date": "2026-12-31",
            "status": "draft",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "수정 프로젝트"
    assert body["manager"] == "새 책임자"
    assert body["code"] == "NEW-001"


def test_project_add_researcher_api_team_only() -> None:
    reset_db()
    team = Team.objects.create(name="우리팀", description="우리팀", join_code="222222")
    other_team = Team.objects.create(name="다른팀", description="다른팀", join_code="333333")

    project = Project.objects.create(
        name="우리팀 프로젝트",
        manager="팀장",
        organization="우리팀",
        company=team,
        code="TEAM-01",
        status="active",
    )

    UserAccount.objects.create(
        username="team-admin",
        display_name="팀관리자",
        email="team-admin@example.com",
        password="secret123",
        role=UserAccount.Role.ADMIN,
        team=team,
        is_approved=True,
    )

    my_member = UserAccount.objects.create(
        username="my-member",
        display_name="우리팀연구원",
        email="my-member@example.com",
        password="secret123",
        role=UserAccount.Role.MEMBER,
        team=team,
        is_approved=True,
    )
    other_member = UserAccount.objects.create(
        username="other-member",
        display_name="다른팀연구원",
        email="other-member@example.com",
        password="secret123",
        role=UserAccount.Role.MEMBER,
        team=other_team,
        is_approved=True,
    )

    login_response = client.post("/login", {"username": "team-admin", "password": "secret123"})
    assert login_response.status_code == 302

    ok_response = client.post(
        f"/api/v1/projects/{project.id}/researchers",
        {"user_id": my_member.id},
    )
    assert ok_response.status_code == 200
    assert ProjectMember.objects.filter(project=project, user=my_member).exists()

    fail_response = client.post(
        f"/api/v1/projects/{project.id}/researchers",
        {"user_id": other_member.id},
    )
    assert fail_response.status_code == 400
    assert "우리팀 연구원만 추가" in fail_response.json()["detail"]

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




def test_project_researchers_add_list_excludes_owner_and_existing_members() -> None:
    reset_db()
    team = Team.objects.create(name="추가목록팀", description="추가", join_code="818181")
    owner = UserAccount.objects.create(
        username="project-owner",
        display_name="프로젝트소유자",
        email="project-owner@example.com",
        password="secret123",
        role=UserAccount.Role.OWNER,
        team=team,
        is_approved=True,
    )
    existing_member = UserAccount.objects.create(
        username="existing-member",
        display_name="기등록연구원",
        email="existing-member@example.com",
        password="secret123",
        role=UserAccount.Role.MEMBER,
        team=team,
        is_approved=True,
    )
    available_member = UserAccount.objects.create(
        username="available-member",
        display_name="추가가능연구원",
        email="available-member@example.com",
        password="secret123",
        role=UserAccount.Role.MEMBER,
        team=team,
        is_approved=True,
    )
    project = Project.objects.create(name="프로젝트", manager="소유자", organization="추가목록팀", company=team, code="P-ADD")
    ProjectMember.objects.create(project=project, user=owner, role="admin")
    ProjectMember.objects.create(project=project, user=existing_member, role="member")

    local_client = Client()
    assert local_client.post("/login", {"username": "project-owner", "password": "secret123"}).status_code == 302
    page = local_client.get(f"/frontend/projects/{project.id}/researchers")
    assert page.status_code == 200
    html = page.content.decode()
    add_section = html.split("집단별 연구자 목록 상세")[0]

    assert "project-owner" not in add_section
    assert "existing-member" not in add_section


def test_project_researchers_page_uses_user_role_label() -> None:
    reset_db()
    team = Team.objects.create(name="역할표시팀", description="역할", join_code="616161")
    admin_user = UserAccount.objects.create(
        username="project-admin-role",
        display_name="프로젝트관리자",
        email="project-admin-role@example.com",
        password="secret123",
        role=UserAccount.Role.ADMIN,
        team=team,
        is_approved=True,
    )
    project = Project.objects.create(name="프로젝트3", manager="관리자", organization="역할표시팀", company=team, code="P-ROLE")
    ProjectMember.objects.create(project=project, user=admin_user, role="member")

    local_client = Client()
    assert local_client.post("/login", {"username": "project-admin-role", "password": "secret123"}).status_code == 302
    page = local_client.get(f"/frontend/projects/{project.id}/researchers")
    assert page.status_code == 200
    html = page.content.decode()
    assert "프로젝트관리자" in html
    assert "관리자" in html


def test_project_researchers_owner_cannot_be_removed() -> None:
    reset_db()
    team = Team.objects.create(name="제외불가팀", description="제외", join_code="717171")
    owner = UserAccount.objects.create(
        username="cannot-remove-owner",
        display_name="제외불가소유자",
        email="cannot-remove-owner@example.com",
        password="secret123",
        role=UserAccount.Role.OWNER,
        team=team,
        is_approved=True,
    )
    project = Project.objects.create(name="프로젝트2", manager="소유자", organization="제외불가팀", company=team, code="P-DEL")
    ProjectMember.objects.create(project=project, user=owner, role="admin")

    local_client = Client()
    assert local_client.post("/login", {"username": "cannot-remove-owner", "password": "secret123"}).status_code == 302
    remove = local_client.post(f"/api/v1/projects/{project.id}/researchers/remove", {"user_id": str(owner.id)})
    assert remove.status_code == 400
    assert "소유자는 프로젝트 연구자에서 제외할 수 없습니다." in remove.json()["detail"]

def test_project_detail_and_viewer_pages() -> None:
    reset_db()
    project_id, note_id = seed_workflow_data()
    login_response = client.post("/login", {"username": "tester", "password": "secret123"})
    assert login_response.status_code == 302

    project_detail = client.get(f"/frontend/projects/{project_id}")
    assert project_detail.status_code == 200
    html = project_detail.content.decode()
    assert "연구노트 업데이트" in html
    assert "집단별 연구자 목록 상세" in html

    viewer_response = client.get(f"/frontend/research-notes/{note_id}/viewer")
    assert viewer_response.status_code == 200
    assert "현재 보기 PDF 저장" in viewer_response.content.decode()


def test_project_create_and_my_page_content() -> None:
    reset_db()
    seed_workflow_data()
    login(client)
    create_page = client.get("/frontend/projects/create")
    assert create_page.status_code == 200
    assert "프로젝트 생성" in create_page.content.decode()

    my_page = client.get("/frontend/my-page")
    assert my_page.status_code in {200, 302}
    if my_page.status_code == 200:
        assert "마이페이지" in my_page.content.decode()
    else:
        assert my_page["Location"] == "/frontend/admin/dashboard"


def test_workflow_apis_support_management_actions() -> None:
    reset_db()
    seed_workflow_data()
    login(client)
    invited_user = UserAccount.objects.exclude(username="member-login").first()

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
            "invited_members": f'[{{"id":{invited_user.id},"role":"admin"}}]',
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
    assert good_login["Location"] in {"/frontend/workflows", "/frontend/admin/dashboard"}

    my_page = anon.get("/frontend/my-page")
    assert my_page.status_code in {200, 302}

    logout = anon.get("/logout")
    assert logout.status_code == 302




def test_my_page_research_note_upload_creates_note_and_file() -> None:
    reset_db()
    local_client = Client()
    login(local_client)

    with tempfile.TemporaryDirectory() as temp_dir:
        with override_settings(RESEARCH_NOTES_STORAGE_ROOT=temp_dir):
            upload = SimpleUploadedFile('upload-note.txt', b'hello research note', content_type='text/plain')
            response = local_client.post('/frontend/my-page/research-note/upload', {'research_note_file': upload})

            assert response.status_code == 201
            body = response.json()
            note_id = body['note_id']
            saved_path = Path(body['file_path'])
            assert saved_path.exists()
            assert saved_path.read_bytes() == b'hello research note'
            assert note_id in str(saved_path.parent)

            note = ResearchNote.objects.get(id=note_id)
            assert note.title == 'upload-note.txt'
            assert ResearchNoteFile.objects.filter(note=note, name='upload-note.txt').exists()


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




def test_researchers_page_shows_owner_at_top() -> None:
    reset_db()
    team = Team.objects.create(name="정렬팀", description="정렬", join_code="919191")
    UserAccount.objects.create(
        username="team-owner",
        display_name="팀소유자",
        email="team-owner@example.com",
        password="secret123",
        role=UserAccount.Role.OWNER,
        team=team,
        is_approved=True,
    )
    UserAccount.objects.create(
        username="team-member",
        display_name="팀일반",
        email="team-member@example.com",
        password="secret123",
        role=UserAccount.Role.MEMBER,
        team=team,
        is_approved=True,
    )

    local_client = Client()
    login_response = local_client.post("/login", {"username": "team-owner", "password": "secret123"})
    assert login_response.status_code == 302

    response = local_client.get("/frontend/researchers")
    assert response.status_code == 200
    html = response.content.decode()

    owner_idx = html.find("team-owner")
    member_idx = html.find("team-member")
    assert owner_idx != -1 and member_idx != -1
    assert owner_idx < member_idx

def test_researchers_page_separated_fields() -> None:
    reset_db()
    seed_workflow_data()
    local_client = Client()
    login(local_client)
    response = local_client.get("/frontend/researchers")
    assert response.status_code == 200
    html = response.content.decode()
    assert "연구자 목록" in html
    assert "회사 연계 승인 대기 사용자 승인" in html
    assert "researcherToast" in html
    assert "member-login" in html
    assert "tester" not in html

    projects_page = local_client.get("/frontend/projects")
    assert projects_page.status_code == 200
    assert "프로젝트 페이지는 프로젝트 정보와 상세 진입만 담당합니다." in projects_page.content.decode()


def test_researchers_support_unassigned_verify_id_and_pending_for_my_team_queries() -> None:
    reset_db()
    team = Team.objects.create(name="코드팀", description="코드기반", join_code="555555")
    UserAccount.objects.create(
        username="no-team",
        display_name="무소속",
        email="no-team@example.com",
        password="secret123",
        role=UserAccount.Role.MEMBER,
        team=None,
        is_approved=False,
    )
    team_pending = UserAccount.objects.create(
        username="pending-code",
        display_name="코드대기",
        email="pending-code@example.com",
        password="secret123",
        role=UserAccount.Role.MEMBER,
        team=team,
        is_approved=False,
    )
    UserAccount.objects.create(
        username="approved-code",
        display_name="코드승인",
        email="approved-code@example.com",
        password="secret123",
        role=UserAccount.Role.MEMBER,
        team=team,
        is_approved=True,
    )

    local_client = Client()
    login(local_client)

    unassigned_response = local_client.get("/api/v1/researchers", {"action": "unassigned", "q": "no-team"})
    assert unassigned_response.status_code == 200
    unassigned_payload = unassigned_response.json()
    assert any(item["username"] == "no-team" for item in unassigned_payload)

    verify_response = local_client.post("/api/v1/researchers", {"action": "verify_id", "username": "no-team"})
    assert verify_response.status_code == 200
    assert verify_response.json()["can_invite"] is False

    pending_response = local_client.get("/api/v1/researchers", {"action": "pending_for_my_team"})
    assert pending_response.status_code == 200
    pending_payload = pending_response.json()
    assert not any(item["id"] == team_pending.id for item in pending_payload)



def test_researchers_pending_for_my_team_includes_linked_unapproved_user() -> None:
    reset_db()
    my_team = Team.objects.create(name="기본팀", description="기본", join_code="123456")
    pending_user = UserAccount.objects.create(
        username="mine-pending",
        display_name="내팀대기",
        email="mine-pending@example.com",
        password="secret123",
        role=UserAccount.Role.MEMBER,
        team=my_team,
        is_approved=False,
    )

    local_client = Client()
    login(local_client)

    response = local_client.get("/api/v1/researchers", {"action": "pending_for_my_team"})
    assert response.status_code == 200
    payload = response.json()
    assert any(item["id"] == pending_user.id for item in payload)


def test_researchers_list_only_my_team_approved_users() -> None:
    reset_db()
    my_team = Team.objects.create(name="기본팀", description="기본", join_code="123456")
    other_team = Team.objects.create(name="다른팀", description="다름", join_code="654321")
    mine = UserAccount.objects.create(
        username="mine-approved",
        display_name="내팀승인",
        email="mine-pending@example.com",
        password="secret123",
        role=UserAccount.Role.MEMBER,
        team=my_team,
        is_approved=True,
    )
    UserAccount.objects.create(
        username="other-approved",
        display_name="타팀승인",
        email="other-pending@example.com",
        password="secret123",
        role=UserAccount.Role.MEMBER,
        team=other_team,
        is_approved=True,
    )
    UserAccount.objects.create(
        username="mine-pending",
        display_name="내팀대기",
        email="mine-pending2@example.com",
        password="secret123",
        role=UserAccount.Role.MEMBER,
        team=my_team,
        is_approved=False,
    )

    local_client = Client()
    login(local_client)
    response = local_client.get("/api/v1/researchers")
    assert response.status_code == 200
    payload = response.json()
    assert any(item["id"] == mine.id for item in payload)
    assert not any(item["username"] == "other-approved" for item in payload)
    assert not any(item["username"] == "mine-pending" for item in payload)


def test_seed_demo_data_populates_tables() -> None:
    reset_db()
    seed_demo_data(reset=True)

    assert Project.objects.count() >= 1
    assert UserAccount.objects.count() >= 2
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

    owner_signup = client.post(
        "/api/v1/auth/signup",
        {
            "username": "leader",
            "display_name": "팀장",
            "email": "leader@example.com",
            "password": "secret123",
            "role": "owner",
            "team_name": "플랫폼팀",
            "team_description": "운영팀",
        },
    )
    assert owner_signup.status_code == 201
    assert owner_signup.json()["team"] == "-"

    local_client = Client()
    admin_login = local_client.post("/admin/login", {"username": "admin", "password": "admin1234"})
    assert admin_login.status_code == 302

    owner_id = UserAccount.objects.get(username="leader").id
    approve = local_client.post("/api/v1/admin/users", {"action": "approve", "user_id": str(owner_id)})
    assert approve.status_code == 200
    join_code = approve.json()["join_code"]
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

    users = local_client.get("/api/v1/admin/users")
    assert users.status_code == 200
    users_payload = users.json()
    assert any(item["username"] == "leader" and item["role"] == "소유자" for item in users_payload)
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
    assert "연구자(사용자) 통합 관리" in users_page.content.decode()

    tables = local_client.get("/api/v1/admin/tables")
    assert tables.status_code == 200
    tables_payload = tables.json()
    assert any(item["table"] == "workflow_app_useraccount" for item in tables_payload)


def test_owner_and_admin_can_grant_admin_role() -> None:
    reset_db()
    owner_signup = client.post(
        "/api/v1/auth/signup",
        {
            "username": "owner1",
            "display_name": "회사소유자",
            "email": "owner1@example.com",
            "password": "secret123",
            "role": "owner",
            "team_name": "권한팀",
            "team_description": "권한테스트",
        },
    )
    assert owner_signup.status_code == 201

    super_client = Client()
    assert super_client.post("/admin/login", {"username": "admin", "password": "admin1234"}).status_code == 302
    owner_id = UserAccount.objects.get(username="owner1").id
    assert super_client.post("/api/v1/admin/users", {"action": "approve", "user_id": str(owner_id)}).status_code == 200

    UserAccount.objects.create(
        username="team-admin-2",
        display_name="팀관리자2",
        email="team-admin-2@example.com",
        password="secret123",
        role=UserAccount.Role.ADMIN,
        team=Team.objects.get(name="권한팀"),
        is_approved=True,
    )
    member_user = UserAccount.objects.create(
        username="grant-member",
        display_name="권한대상",
        email="grant-member@example.com",
        password="secret123",
        role=UserAccount.Role.MEMBER,
        team=Team.objects.get(name="권한팀"),
        is_approved=True,
    )

    # super admin 승인 완료 후 owner 로그인 가능

    owner_client = Client()
    assert owner_client.post("/login", {"username": "owner1", "password": "secret123"}).status_code == 302
    grant_by_owner = owner_client.post("/api/v1/researchers", {"action": "grant_role", "user_id": str(member_user.id), "role": "admin"})
    assert grant_by_owner.status_code == 200
    member_user.refresh_from_db()
    assert member_user.role == UserAccount.Role.ADMIN

    member_user.role = UserAccount.Role.MEMBER
    member_user.save(update_fields=["role", "updated_at"])

    admin_client = Client()
    assert admin_client.post("/login", {"username": "team-admin-2", "password": "secret123"}).status_code == 302
    grant_by_admin = admin_client.post("/api/v1/researchers", {"action": "grant_role", "user_id": str(member_user.id), "role": "admin"})
    assert grant_by_admin.status_code == 200
    member_user.refresh_from_db()
    assert member_user.role == UserAccount.Role.ADMIN



def test_super_admin_can_search_and_assign_user_team() -> None:
    reset_db()
    team = Team.objects.create(name="검색팀", description="검색용", join_code="654321")
    user = UserAccount.objects.create(
        username="search-user",
        display_name="검색 사용자",
        email="search-user@example.com",
        password="secret123",
        role=UserAccount.Role.MEMBER,
    )

    admin_client = Client()
    login_response = admin_client.post("/admin/login", {"username": "admin", "password": "admin1234"})
    assert login_response.status_code == 302

    search_response = admin_client.get("/api/v1/admin/users", {"q": "search-user"})
    assert search_response.status_code == 200
    payload = search_response.json()
    assert len(payload) == 1
    assert payload[0]["username"] == "search-user"

    assign_response = admin_client.post(
        "/api/v1/admin/users",
        {
            "user_id": str(user.id),
            "team_id": str(team.id),
        },
    )
    assert assign_response.status_code == 200
    assert assign_response.json()["team"] == "검색팀"

    user.refresh_from_db()
    assert user.team_id == team.id


def test_super_admin_can_approve_grant_and_expel_user() -> None:
    reset_db()
    team = Team.objects.create(name="승인팀", description="승인용", join_code="777777")
    user = UserAccount.objects.create(
        username="pending-user",
        display_name="대기 사용자",
        email="pending-user@example.com",
        password="secret123",
        role=UserAccount.Role.MEMBER,
        team=team,
        is_approved=False,
    )

    admin_client = Client()
    assert admin_client.post("/admin/login", {"username": "admin", "password": "admin1234"}).status_code == 302

    approve = admin_client.post("/api/v1/admin/users", {"action": "approve", "user_id": str(user.id)})
    assert approve.status_code == 200

    grant = admin_client.post("/api/v1/admin/users", {"action": "grant_role", "user_id": str(user.id), "role": "admin"})
    assert grant.status_code == 200

    expel = admin_client.post("/api/v1/admin/users", {"action": "expel", "user_id": str(user.id)})
    assert expel.status_code == 200
    assert not UserAccount.objects.filter(id=user.id).exists()


def test_auth_session_bridge_login_me_logout_api() -> None:
    reset_db()
    team = Team.objects.create(name="브릿지팀", description="브릿지", join_code="989898")
    UserAccount.objects.create(
        username="bridge-user",
        display_name="브릿지유저",
        email="bridge-user@example.com",
        password=make_password("secret123"),
        role=UserAccount.Role.MEMBER,
        team=team,
        is_approved=True,
    )

    login_res = client.post('/api/v1/auth/login', {'username': 'bridge-user', 'password': 'secret123'})
    assert login_res.status_code == 200

    me_res = client.get('/api/v1/auth/me')
    assert me_res.status_code == 200
    assert me_res.json()['user']['username'] == 'bridge-user'

    logout_res = client.post('/api/v1/auth/logout')
    assert logout_res.status_code == 200

    me_after = client.get('/api/v1/auth/me')
    assert me_after.status_code == 401


def test_research_note_files_api_returns_note_file_rows() -> None:
    reset_db()
    _, note_id = seed_workflow_data()

    assert client.post("/api/v1/auth/login", {"username": "tester", "password": "secret123"}).status_code == 200
    response = client.get(f"/api/v1/research-notes/{note_id}/files")
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert payload
    assert payload[0]["name"] == "sample.pdf"


def test_project_research_files_api_returns_tokens_and_labels() -> None:
    reset_db()
    project_id, _ = seed_workflow_data()
    assert client.post("/api/v1/auth/login", {"username": "tester", "password": "secret123"}).status_code == 200

    response = client.get(f"/api/v1/projects/{project_id}/research-files")
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert payload
    assert ":" in payload[0]["token"]
    assert payload[0]["label"].startswith("[")


def test_frontend_routes_are_redirected_to_web_app_origin() -> None:
    response = client.get('/frontend/projects', {'tab': 'all'})
    assert response.status_code == 302
    assert response['Location'] == 'http://127.0.0.1:3000/frontend/projects?tab=all'


@override_settings(WEB_APP_ORIGIN='https://web.example.com')
def test_frontend_routes_respect_configured_web_app_origin() -> None:
    response = client.get('/frontend/research-notes/abc/viewer')
    assert response.status_code == 302
    assert response['Location'] == 'https://web.example.com/frontend/research-notes/abc/viewer'
