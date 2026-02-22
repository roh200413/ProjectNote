from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from server.core.dependencies import repository
from server.core.http import admin_required_page


@require_http_methods(["GET", "POST"])
@admin_required_page
def admin_teams_api(_request):
    return JsonResponse({"detail": "슈퍼 어드민은 테이블 관리만 가능합니다."}, status=403)


@require_http_methods(["GET", "POST"])
@admin_required_page
def admin_users_api(request):
    if request.method == "GET":
        keyword = request.GET.get("q", "").strip()
        return JsonResponse(repository.list_all_users(keyword=keyword), safe=False)

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
        payload = repository.assign_user_team(user_id=int(user_id), team_id=team_id)
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)
    return JsonResponse(payload)


@require_http_methods(["GET"])
@admin_required_page
def admin_tables_api(_request):
    return JsonResponse(repository.list_managed_tables(), safe=False)


@require_http_methods(["POST"])
@admin_required_page
def admin_table_truncate_api(_request, table_name: str):
    try:
        repository.truncate_table(table_name)
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)
    return JsonResponse({"message": f"{table_name} 테이블 데이터가 삭제되었습니다."})
