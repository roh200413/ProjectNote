from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods

from server.application.models import ResearchNote
from server.application.web_support import login_required_page, page_context, repository


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
    return render(
        request,
        "research_notes/detail.html",
        page_context(
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
    if not files:
        raise Http404("Research note file not found")

    requested_file = request.GET.get("file")
    selected_file = files[0]
    if requested_file:
        matched = next((item for item in files if item["id"] == requested_file), None)
        if matched:
            selected_file = matched

    return render(
        request,
        "research_notes/viewer.html",
        page_context(
            request,
            {
                "note": note,
                "files": files,
                "selected_file": selected_file,
                "folders": repository.list_note_folders(note_id),
            },
        ),
    )
