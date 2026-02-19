import os
import uuid
import json
from pathlib import Path
from datetime import datetime, timezone
from functools import wraps

from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods

from projectnote.workflow_app.models import Project, ResearchNote
from projectnote.workflow_app.infrastructure.repositories import WorkflowRepository
from projectnote.workflow_app.application.services import WorkflowService

repository = WorkflowRepository()
service = WorkflowService(repository)

SUPER_ADMIN_JSON_PATH = Path(__file__).resolve().parent.parent / "super_admin_accounts.json"


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
            "role": "관리자",
            "email": os.getenv("PROJECTNOTE_DEMO_EMAIL", "paul@deep-ai.kr"),
            "organization": os.getenv("PROJECTNOTE_DEMO_ORG", "(주)딥아이"),
            "major": os.getenv("PROJECTNOTE_DEMO_MAJOR", "R&D"),
        }
    }


def _page_context(request, extra: dict | None = None) -> dict:
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
        if not request.session.get("user_profile"):
            next_url = request.get_full_path()
            return redirect(f"/login?next={next_url}")
        return view_func(request, *args, **kwargs)

    return _wrapped


def _json_uuid_validation_error(field: str, raw_input: str) -> JsonResponse:
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


@require_GET
def health(_request):
    return JsonResponse({"status": "ok"})


@require_http_methods(["GET", "POST"])
@ensure_csrf_cookie
def login_page(request):
    if request.method == "GET":
        if request.session.get("user_profile"):
            return redirect("/frontend/workflows")
        return render(request, "auth/login.html", {"error": "", "next": request.GET.get("next", "")})

    username = request.POST.get("username", "").strip()
    password = request.POST.get("password", "")
    next_url = request.POST.get("next", "")
    user = repository.find_user_for_login(username, password)
    if not user:
        user = _load_super_admin_users().get(username)
        if not user or user["password"] != password:
            return render(
                request,
                "auth/login.html",
                {"error": "아이디 또는 비밀번호가 올바르지 않습니다.", "next": next_url},
                status=401,
            )

    request.session["user_profile"] = {
        "username": username,
        "name": user["name"],
        "role": user["role"],
        "email": user["email"],
        "organization": user["organization"],
        "major": user["major"],
        "signature_data_url": request.session.get("user_profile", {}).get("signature_data_url", ""),
    }
    if next_url.startswith("/"):
        return redirect(next_url)
    return redirect("/frontend/workflows")




@require_GET
@ensure_csrf_cookie
def signup_page(request):
    if request.session.get("user_profile"):
        return redirect("/frontend/workflows")
    return render(request, "auth/signup.html", {"next": request.GET.get("next", "")})


@require_GET
def logout_page(request):
    request.session.pop("user_profile", None)
    return redirect("/login")


@require_http_methods(["POST"])
def signup_api(request):
    username = request.POST.get("username", "").strip()
    display_name = request.POST.get("display_name", "").strip()
    email = request.POST.get("email", "").strip()
    password = request.POST.get("password", "").strip()
    role = request.POST.get("role", "member").strip()
    if not all([username, display_name, email, password]):
        return JsonResponse({"detail": "username/display_name/email/password는 필수입니다."}, status=400)

    try:
        registered = repository.register_user(
            username=username,
            display_name=display_name,
            email=email,
            password=password,
            role=role,
            team_name=request.POST.get("team_name", "").strip(),
            team_description=request.POST.get("team_description", "").strip(),
            team_code=request.POST.get("team_code", "").strip(),
        )
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)

    return JsonResponse(registered, status=201)


@require_GET
def frontend_bootstrap(_request):
    return JsonResponse(
        {
            "api_name": "ProjectNote API",
            "api_version": "v1",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


@require_GET
def dashboard_summary(_request):
    return JsonResponse(repository.dashboard_counts())


@require_GET
def projects(request):
    org_id = request.GET.get("org_id")
    if org_id:
        try:
            uuid.UUID(org_id)
        except ValueError:
            return _json_uuid_validation_error("org_id", org_id)
    return JsonResponse(repository.list_projects(), safe=False)


@require_http_methods(["GET", "POST"])
def project_management_api(request):
    if request.method == "GET":
        return JsonResponse(repository.list_projects(), safe=False)
    project = service.create_project(request.POST)
    return JsonResponse(project, status=201)


@require_http_methods(["GET", "POST"])
def researchers_api(request):
    if request.method == "GET":
        return JsonResponse(repository.list_researchers(), safe=False)
    return JsonResponse(repository.create_researcher(request.POST), status=201)


@require_http_methods(["GET", "POST"])
def data_updates_api(request):
    if request.method == "GET":
        return JsonResponse(repository.list_data_updates(), safe=False)
    return JsonResponse(repository.create_data_update(request.POST), status=201)


@require_GET
def final_download_api(_request):
    payload = {
        "format": "pdf",
        "status": "ready",
        "download_url": "/downloads/projectnote-final-report.pdf",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    return JsonResponse(payload)


@require_http_methods(["GET", "POST"])
def signature_api(request):
    if request.method == "GET":
        return JsonResponse(repository.read_signature())
    payload = repository.update_signature(
        signed_by=request.POST.get("signed_by", ""), status=request.POST.get("status", "valid")
    )
    return JsonResponse(payload)




@require_http_methods(["GET", "POST"])
@login_required_page
def admin_teams_api(request):
    if request.method == "GET":
        return JsonResponse(repository.list_teams(), safe=False)

    name = request.POST.get("name", "").strip()
    if not name:
        return JsonResponse({"detail": "팀 이름은 필수입니다."}, status=400)
    team = repository.create_team(name=name, description=request.POST.get("description", "").strip())
    return JsonResponse(team, status=201)


@require_http_methods(["GET", "POST"])
@login_required_page
def admin_users_api(request):
    if request.method == "GET":
        return JsonResponse(repository.list_all_users(), safe=False)

    username = request.POST.get("username", "").strip()
    display_name = request.POST.get("display_name", "").strip()
    email = request.POST.get("email", "").strip()
    password = request.POST.get("password", "").strip()
    if not all([username, display_name, email, password]):
        return JsonResponse({"detail": "username/display_name/email/password는 필수입니다."}, status=400)

    try:
        admin = repository.create_initial_admin(
            username=username,
            display_name=display_name,
            email=email,
            password=password,
            team_id=request.POST.get("team_id") or None,
        )
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=409)
    return JsonResponse(admin, status=201)


@require_http_methods(["GET"])
@login_required_page
def admin_tables_api(_request):
    return JsonResponse(repository.list_managed_tables(), safe=False)


@require_http_methods(["POST"])
@login_required_page
def admin_table_truncate_api(_request, table_name: str):
    try:
        repository.truncate_table(table_name)
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)
    return JsonResponse({"message": f"{table_name} 테이블 데이터가 삭제되었습니다."})

@require_GET
def research_notes_api(_request):
    return JsonResponse(repository.list_research_notes(), safe=False)


@require_GET
def research_note_detail_api(_request, note_id: str):
    try:
        return JsonResponse(repository.get_research_note(note_id))
    except ResearchNote.DoesNotExist as exc:
        raise Http404("Research note not found") from exc


@require_http_methods(["POST"])
def research_note_update_api(request, note_id: str):
    try:
        note = repository.update_research_note(note_id, request.POST.get("title"), request.POST.get("summary"))
    except ResearchNote.DoesNotExist as exc:
        raise Http404("Research note not found") from exc
    return JsonResponse({"message": "연구노트가 업데이트되었습니다.", "note": note})


@require_GET
@ensure_csrf_cookie
@login_required_page
def workflow_home_page(request):
    cards = [
        {"title": "프로젝트 생성", "href": "/frontend/projects/create", "description": "신규 프로젝트를 생성합니다."},
        {"title": "프로젝트 관리", "href": "/frontend/projects", "description": "생성된 프로젝트 목록/상세를 관리합니다."},
        {"title": "연구자 관리", "href": "/frontend/researchers", "description": "연구자 등록 및 소속/역할 정보를 관리합니다."},
        {"title": "데이터 업데이트", "href": "/frontend/data-updates", "description": "데이터 업데이트 이력을 기록합니다."},
        {"title": "연구노트 최종 다운로드", "href": "/frontend/final-download", "description": "최종 산출물 생성 상태를 확인합니다."},
        {"title": "사인 업데이트", "href": "/frontend/signatures", "description": "최신 서명 상태를 갱신합니다."},
        {"title": "My Page", "href": "/frontend/my-page", "description": "내 상세 정보와 전자서명을 확인합니다."},
        {"title": "ADMIN", "href": "/frontend/admin", "description": "운영 지표와 최근 액션을 조회합니다."},
    ]
    return render(request, "workflow/home.html", _page_context(request, {"cards": cards}))


@require_GET
@ensure_csrf_cookie
@login_required_page
def admin_page(request):
    return redirect("/frontend/admin/dashboard")


def _admin_navigation(current: str) -> list[dict[str, str]]:
    items = [
        {"key": "dashboard", "title": "대시보드", "href": "/frontend/admin/dashboard"},
        {"key": "teams", "title": "팀 관리", "href": "/frontend/admin/teams"},
        {"key": "users", "title": "가입자 관리", "href": "/frontend/admin/users"},
        {"key": "tables", "title": "테이블 관리", "href": "/frontend/admin/tables"},
    ]
    for item in items:
        item["active"] = item["key"] == current
    return items


@require_GET
@ensure_csrf_cookie
@login_required_page
def admin_dashboard_page(request):
    return render(
        request,
        "admin/dashboard.html",
        _page_context(
            request,
            {
                "summary": repository.dashboard_counts(),
                "admin_nav_items": _admin_navigation("dashboard"),
            },
        ),
    )


@require_GET
@ensure_csrf_cookie
@login_required_page
def admin_teams_page(request):
    return render(
        request,
        "admin/teams.html",
        _page_context(request, {"teams": repository.list_teams(), "admin_nav_items": _admin_navigation("teams")}),
    )


@require_GET
@ensure_csrf_cookie
@login_required_page
def admin_users_page(request):
    return render(
        request,
        "admin/users.html",
        _page_context(
            request,
            {"admin_accounts": repository.list_all_users(), "admin_nav_items": _admin_navigation("users")},
        ),
    )


@require_GET
@ensure_csrf_cookie
@login_required_page
def admin_tables_page(request):
    return render(
        request,
        "admin/tables.html",
        _page_context(request, {"tables": repository.list_managed_tables(), "admin_nav_items": _admin_navigation("tables")}),
    )


@require_GET
@ensure_csrf_cookie
@login_required_page
def project_management_page(request):
    return render(request, "workflow/projects.html", _page_context(request, {"projects": repository.list_projects()}))


@require_GET
@ensure_csrf_cookie
@login_required_page
def project_create_page(request):
    return render(
        request,
        "workflow/project_create.html",
        _page_context(request, {"researcher_groups": repository.researcher_groups_for_selection()}),
    )


@require_GET
@ensure_csrf_cookie
@login_required_page
def project_detail_page(request, project_id: str):
    try:
        project = repository.project_to_dict(Project.objects.get(id=project_id))
    except Project.DoesNotExist as exc:
        raise Http404("Project not found") from exc

    note_ids = repository.project_note_ids(project_id)
    all_notes = repository.list_research_notes()
    project_notes = [note for note in all_notes if note["id"] in note_ids]
    selected_note = project_notes[0] if project_notes else None
    selected_note_files = repository.list_note_files(selected_note["id"]) if selected_note else []
    return render(
        request,
        "workflow/project_detail.html",
        _page_context(
            request,
            {
                "project": project,
                "project_notes": project_notes,
                "researcher_groups": repository.project_researcher_groups(project_id),
                "selected_note": selected_note,
                "selected_note_files": selected_note_files,
            },
        ),
    )


@require_GET
@ensure_csrf_cookie
@login_required_page
def researchers_page(request):
    return render(request, "workflow/researchers.html", _page_context(request, {"researchers": repository.list_researchers()}))


@require_GET
@ensure_csrf_cookie
@login_required_page
def data_updates_page(request):
    return render(request, "workflow/data_updates.html", _page_context(request, {"updates": repository.list_data_updates()}))


@require_GET
@ensure_csrf_cookie
@login_required_page
def final_download_page(request):
    return render(
        request,
        "workflow/final_download.html",
        _page_context(request, {"report_name": "projectnote-final-report.pdf"}),
    )


@require_GET
@ensure_csrf_cookie
@login_required_page
def signature_page(request):
    return render(request, "workflow/signatures.html", _page_context(request, {"signature": repository.read_signature()}))


@require_GET
@ensure_csrf_cookie
@login_required_page
def my_page(request):
    profile = request.session.get("user_profile", {}).copy()
    profile["signature"] = profile.get("signature_data_url", "")
    return render(request, "workflow/my_page.html", _page_context(request, {"profile": profile}))


@require_http_methods(["POST"])
@login_required_page
def update_my_signature(request):
    signature_data_url = request.POST.get("signature_data_url", "")
    if not signature_data_url.startswith("data:image/"):
        return JsonResponse({"message": "유효한 이미지 데이터가 아닙니다."}, status=400)

    profile = request.session.get("user_profile", {}).copy()
    profile["signature_data_url"] = signature_data_url
    request.session["user_profile"] = profile
    return JsonResponse({"message": "서명이 업데이트되었습니다."})


@require_GET
@ensure_csrf_cookie
@login_required_page
def research_notes_page(request):
    return render(request, "research_notes/list.html", _page_context(request, {"notes": repository.list_research_notes()}))


@require_GET
@ensure_csrf_cookie
@login_required_page
def research_note_detail_page(request, note_id: str):
    try:
        note = repository.get_research_note(note_id)
    except ResearchNote.DoesNotExist as exc:
        raise Http404("Research note not found") from exc
    return render(
        request,
        "research_notes/detail.html",
        _page_context(
            request,
            {
                "note": note,
                "files": repository.list_note_files(note_id),
                "folders": repository.list_note_folders(note_id),
            },
        ),
    )


@require_GET
@ensure_csrf_cookie
@login_required_page
def research_note_viewer_page(request, note_id: str):
    try:
        note = repository.get_research_note(note_id)
    except ResearchNote.DoesNotExist as exc:
        raise Http404("Research note not found") from exc
    files = repository.list_note_files(note_id)
    return render(
        request,
        "research_notes/viewer.html",
        _page_context(request, {"note": note, "file": files[0] if files else None}),
    )
