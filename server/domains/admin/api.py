from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods

from server.application.web_support import admin_repository, admin_required_page, dashboard_counts, page_context


def _admin_navigation(current: str) -> list[dict[str, str]]:
    items = [
        {"key": "dashboard", "title": "대시보드", "href": "/frontend/admin/dashboard"},
        {"key": "users", "title": "사용자 관리", "href": "/frontend/admin/users"},
        {"key": "teams", "title": "팀 관리", "href": "/frontend/admin/teams"},
        {"key": "tables", "title": "테이블 관리", "href": "/frontend/admin/tables"},
    ]
    for item in items:
        item["active"] = item["key"] == current
    return items


@require_http_methods(["GET", "POST"])
@admin_required_page
def admin_teams_api(request):
    return JsonResponse({"detail": "슈퍼 어드민은 테이블 관리만 가능합니다."}, status=403)


@require_http_methods(["GET", "POST"])
@admin_required_page
def admin_users_api(request):
    if request.method == "GET":
        keyword = request.GET.get("q", "").strip()
        return JsonResponse(admin_repository.list_all_users(keyword=keyword), safe=False)

    user_id = request.POST.get("user_id", "").strip()
    team_id_raw = request.POST.get("team_id", "").strip()
    if not user_id.isdigit():
        return JsonResponse({"detail": "유효한 사용자 ID가 필요합니다."}, status=400)

    team_id = None
    if team_id_raw:
        if not team_id_raw.isdigit():
            return JsonResponse({"detail": "유효한 팀 ID가 필요합니다."}, status=400)
        team_id = int(team_id_raw)

    try:
        payload = admin_repository.assign_user_team(user_id=int(user_id), team_id=team_id)
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)
    return JsonResponse(payload)


@require_GET
@admin_required_page
def admin_tables_api(_request):
    return JsonResponse(admin_repository.list_managed_tables(), safe=False)


@require_http_methods(["POST"])
@admin_required_page
def admin_table_truncate_api(_request, table_name: str):
    try:
        admin_repository.truncate_table(table_name)
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)
    return JsonResponse({"message": f"{table_name} 테이블 데이터가 삭제되었습니다."})


@require_GET
@ensure_csrf_cookie
@admin_required_page
def admin_page(_request):
    return redirect("/frontend/admin/dashboard")


@require_GET
@ensure_csrf_cookie
@admin_required_page
def admin_dashboard_page(request):
    return render(
        request,
        "admin/dashboard.html",
        page_context(
            request,
            {
                "summary": dashboard_counts(),
                "admin_nav_items": _admin_navigation("dashboard"),
            },
        ),
    )


@require_GET
@ensure_csrf_cookie
@admin_required_page
def admin_teams_page(request):
    return render(
        request,
        "admin/teams.html",
        page_context(request, {"teams": admin_repository.list_teams(), "admin_nav_items": _admin_navigation("teams")}),
    )


@require_GET
@ensure_csrf_cookie
@admin_required_page
def admin_users_page(request):
    keyword = request.GET.get("q", "").strip()
    return render(
        request,
        "admin/users.html",
        page_context(
            request,
            {
                "admin_accounts": admin_repository.list_all_users(keyword=keyword),
                "teams": admin_repository.list_teams(),
                "keyword": keyword,
                "admin_nav_items": _admin_navigation("users"),
            },
        ),
    )


@require_GET
@ensure_csrf_cookie
@admin_required_page
def admin_tables_page(request):
    return render(
        request,
        "admin/tables.html",
        page_context(request, {"tables": admin_repository.list_managed_tables(), "admin_nav_items": _admin_navigation("tables")}),
    )
