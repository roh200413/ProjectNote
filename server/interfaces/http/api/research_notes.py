from django.http import Http404, JsonResponse
from django.views.decorators.http import require_GET, require_http_methods

from server.core.dependencies import repository
from projectnote.workflow_app.models import ResearchNote


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
