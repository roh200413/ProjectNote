from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods

from projectnote.client.interfaces.common import page_context
from projectnote.server.core.dependencies import authenticate_login_user, authenticate_super_admin, repository
from projectnote.server.core.http import admin_required_page, login_required_page, save_login_session
from projectnote.workflow_app.models import Project, ResearchNote


@require_http_methods(["GET", "POST"])
@ensure_csrf_cookie
def login_page(request):
    if request.method == "GET":
        user_profile = request.session.get("user_profile")
        if user_profile:
            if user_profile.get("is_super_admin"):
                return redirect("/frontend/admin/dashboard")
            return redirect("/frontend/workflows")
        return render(request, "auth/login.html", {"error": "", "next": request.GET.get("next", "")})

    username = request.POST.get("username", "").strip()
    password = request.POST.get("password", "")
    next_url = request.POST.get("next", "")
    user = authenticate_login_user(username, password)
    if not user:
        return render(
            request,
            "auth/login.html",
            {"error": "아이디 또는 비밀번호가 올바르지 않습니다.", "next": next_url},
            status=401,
        )

    if not user.get("is_super_admin") and user.get("team") in {None, "-", ""}:
        return render(
            request,
            "auth/login.html",
            {"error": "관리자 팀 할당 및 승인이 되지 않았습니다.", "next": next_url},
            status=403,
        )

    save_login_session(request, username, user)
    if next_url.startswith("/"):
        return redirect(next_url)
    return redirect("/frontend/workflows")


@require_http_methods(["GET", "POST"])
@ensure_csrf_cookie
def admin_login_page(request):
    if request.method == "GET":
        if request.session.get("user_profile", {}).get("is_super_admin"):
            return redirect("/frontend/admin/dashboard")
        return render(request, "auth/admin_login.html", {"error": "", "next": request.GET.get("next", "")})

    username = request.POST.get("username", "").strip()
    password = request.POST.get("password", "")
    next_url = request.POST.get("next", "")
    user = authenticate_super_admin(username, password)
    if not user:
        return render(
            request,
            "auth/admin_login.html",
            {"error": "슈퍼 어드민 계정으로만 로그인할 수 있습니다.", "next": next_url},
            status=401,
        )

    save_login_session(request, username, user)
    if next_url.startswith("/frontend/admin"):
        return redirect(next_url)
    return redirect("/frontend/admin/dashboard")


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
    return render(request, "workflow/home.html", page_context(request, {"cards": cards}))


@require_GET
@ensure_csrf_cookie
@admin_required_page
def admin_page(_request):
    return redirect("/frontend/admin/dashboard")


def _admin_navigation(current: str) -> list[dict[str, str]]:
    items = [
        {"key": "dashboard", "title": "대시보드", "href": "/frontend/admin/dashboard"},
        {"key": "users", "title": "사용자 관리", "href": "/frontend/admin/users"},
        {"key": "tables", "title": "테이블 관리", "href": "/frontend/admin/tables"},
    ]
    for item in items:
        item["active"] = item["key"] == current
    return items


@require_GET
@ensure_csrf_cookie
@admin_required_page
def admin_dashboard_page(request):
    return render(
        request,
        "admin/dashboard.html",
        page_context(request, {"summary": repository.dashboard_counts(), "admin_nav_items": _admin_navigation("dashboard")}),
    )


@require_GET
@ensure_csrf_cookie
@admin_required_page
def admin_teams_page(request):
    return render(request, "admin/teams.html", page_context(request, {"teams": repository.list_teams(), "admin_nav_items": _admin_navigation("teams")}))


@require_GET
@ensure_csrf_cookie
@admin_required_page
def admin_users_page(request):
    keyword = request.GET.get("q", "").strip()
    return render(
        request,
        "admin/users.html",
        page_context(request, {"admin_accounts": repository.list_all_users(keyword=keyword), "teams": repository.list_teams(), "keyword": keyword, "admin_nav_items": _admin_navigation("users")}),
    )


@require_GET
@ensure_csrf_cookie
@admin_required_page
def admin_tables_page(request):
    return render(request, "admin/tables.html", page_context(request, {"tables": repository.list_managed_tables(), "admin_nav_items": _admin_navigation("tables")}))


@require_GET
@ensure_csrf_cookie
@login_required_page
def project_management_page(request):
    return render(request, "workflow/projects.html", page_context(request, {"projects": repository.list_projects()}))


@require_GET
@ensure_csrf_cookie
@login_required_page
def project_create_page(request):
    return render(request, "workflow/project_create.html", page_context(request, {"researcher_groups": repository.researcher_groups_for_selection()}))


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
        page_context(
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
    return render(request, "workflow/researchers.html", page_context(request, {"researchers": repository.list_researchers()}))


@require_GET
@ensure_csrf_cookie
@login_required_page
def data_updates_page(request):
    return render(request, "workflow/data_updates.html", page_context(request, {"updates": repository.list_data_updates()}))


@require_GET
@ensure_csrf_cookie
@login_required_page
def final_download_page(request):
    return render(request, "workflow/final_download.html", page_context(request, {"report_name": "projectnote-final-report.pdf"}))


@require_GET
@ensure_csrf_cookie
@login_required_page
def signature_page(request):
    return render(request, "workflow/signatures.html", page_context(request, {"signature": repository.read_signature()}))


@require_GET
@ensure_csrf_cookie
@login_required_page
def my_page(request):
    profile = request.session.get("user_profile", {}).copy()
    profile["signature"] = profile.get("signature_data_url", "")
    return render(request, "workflow/my_page.html", page_context(request, {"profile": profile}))


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
    return render(request, "research_notes/list.html", page_context(request, {"notes": repository.list_research_notes()}))


@require_GET
@ensure_csrf_cookie
@login_required_page
def research_note_detail_page(request, note_id: str):
    try:
        note = repository.get_research_note(note_id)
    except ResearchNote.DoesNotExist as exc:
        raise Http404("Research note not found") from exc
    return render(request, "research_notes/detail.html", page_context(request, {"note": note, "files": repository.list_note_files(note_id), "folders": repository.list_note_folders(note_id)}))


@require_GET
@ensure_csrf_cookie
@login_required_page
def research_note_viewer_page(request, note_id: str):
    try:
        note = repository.get_research_note(note_id)
    except ResearchNote.DoesNotExist as exc:
        raise Http404("Research note not found") from exc
    files = repository.list_note_files(note_id)
    return render(request, "research_notes/viewer.html", page_context(request, {"note": note, "file": files[0] if files else None}))
