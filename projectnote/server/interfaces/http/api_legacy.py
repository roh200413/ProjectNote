import uuid
from datetime import datetime, timezone

from django.http import Http404, JsonResponse
from django.views.decorators.http import require_GET, require_http_methods

from projectnote.workflow_app.models import ResearchNote

from .common import admin_required_page, json_uuid_validation_error, repository, service


@require_GET
def health(_request):
    return JsonResponse({"status": "ok"})


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
            return json_uuid_validation_error("org_id", org_id)
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
@admin_required_page
def admin_teams_api(request):
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
