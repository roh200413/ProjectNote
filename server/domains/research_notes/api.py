import mimetypes
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods

from .models import ResearchNote
from server.domains.admin.models import UserAccount
from server.application.web_support import login_required_page, page_context, research_note_repository, signature_repository


@require_GET
def research_notes_api(_request):
    return JsonResponse(research_note_repository.list_research_notes(), safe=False)


@require_GET
def research_note_detail_api(_request, note_id: str):
    try:
        return JsonResponse(research_note_repository.get_research_note(note_id))
    except ResearchNote.DoesNotExist as exc:
        raise Http404("Research note not found") from exc


@require_http_methods(["POST"])
def research_note_update_api(request, note_id: str):
    try:
        note = research_note_repository.update_research_note(note_id, request.POST.get("title"), request.POST.get("summary"))
    except ResearchNote.DoesNotExist as exc:
        raise Http404("Research note not found") from exc
    return JsonResponse({"message": "연구노트가 업데이트되었습니다.", "note": note})


@require_GET
@ensure_csrf_cookie
@login_required_page
def research_notes_page(request):
    return render(request, "research_notes/list.html", page_context(request, {"notes": research_note_repository.list_research_notes()}))


@require_GET
@ensure_csrf_cookie
@login_required_page
def research_note_detail_page(request, note_id: str):
    try:
        note = research_note_repository.get_research_note(note_id)
    except ResearchNote.DoesNotExist as exc:
        raise Http404("Research note not found") from exc
    return render(
        request,
        "research_notes/detail.html",
        page_context(
            request,
            {
                "note": note,
                "files": research_note_repository.list_note_files(note_id),
                "folders": research_note_repository.list_note_folders(note_id),
            },
        ),
    )


@require_GET
@ensure_csrf_cookie
@login_required_page
def research_note_viewer_page(request, note_id: str):
    try:
        note = research_note_repository.get_research_note(note_id)
    except ResearchNote.DoesNotExist as exc:
        raise Http404("Research note not found") from exc

    files = research_note_repository.list_note_files(note_id)
    if not files:
        raise Http404("Research note file not found")

    requested_file = request.GET.get("file")
    selected_file = files[0]
    if requested_file:
        matched = next((item for item in files if item["id"] == requested_file), None)
        if matched:
            selected_file = matched

    selected_file_url = f"/frontend/research-notes/{note_id}/files/{selected_file['id']}/content"

    note_obj = ResearchNote.objects.select_related("project").filter(id=note_id).first()
    manager_raw = (note_obj.project.manager if note_obj and note_obj.project else "") if note_obj else ""

    author_user = UserAccount.objects.filter(username=selected_file.get("author", "")).first()
    if not author_user:
        author_user = UserAccount.objects.filter(display_name=selected_file.get("author", "")).first()

    manager_user = UserAccount.objects.filter(username=manager_raw).first()
    if not manager_user:
        manager_user = UserAccount.objects.filter(display_name=manager_raw).first()

    author_signature = signature_repository.read_signature(author_user.username) if author_user else {"signature_data_url": ""}
    manager_signature = signature_repository.read_signature(manager_user.username) if manager_user else {"signature_data_url": ""}
    reviewer_date = datetime.now().strftime("%Y.%m.%d / %I:%M %p")

    return render(
        request,
        "research_notes/viewer.html",
        page_context(
            request,
            {
                "note": note,
                "files": files,
                "file": selected_file,
                "selected_file": selected_file,
                "selected_file_url": selected_file_url,
                "folders": research_note_repository.list_note_folders(note_id),
                "manager_name": manager_user.display_name if manager_user else manager_raw,
                "author_signature_data_url": author_signature.get("signature_data_url", ""),
                "manager_signature_data_url": manager_signature.get("signature_data_url", ""),
                "author_date": selected_file.get("created", "-"),
                "reviewer_date": reviewer_date,
            },
        ),
    )


@require_GET
@ensure_csrf_cookie
@login_required_page
def research_note_file_content_page(request, note_id: str, file_id: str):
    try:
        note_file = research_note_repository.get_note_file(note_id, file_id)
    except Exception as exc:
        raise Http404("Research note file not found") from exc

    safe_name = Path(note_file["name"]).name
    candidates = [Path(folder) / safe_name for folder in research_note_repository.list_note_folders(note_id)]
    if not candidates:
        storage_root = Path(settings.RESEARCH_NOTES_STORAGE_ROOT)
        candidates = list(storage_root.glob(f"*/{note_id}/{safe_name}"))

    source = next((c for c in candidates if c.exists() and c.is_file()), None)
    if not source:
        raise Http404("Research note file content not found")

    content_type = mimetypes.guess_type(safe_name)[0] or "application/octet-stream"
    as_attachment = request.GET.get("download") == "1"
    return FileResponse(source.open("rb"), as_attachment=as_attachment, filename=safe_name, content_type=content_type)


@require_http_methods(["POST"])
def research_note_file_update_api(request, note_id: str, file_id: str):
    try:
        updated = research_note_repository.update_note_file(
            note_id,
            file_id,
            request.POST.get("author"),
            request.POST.get("created"),
        )
    except Exception as exc:
        raise Http404("Research note file not found") from exc
    return JsonResponse({"message": "파일 정보가 업데이트되었습니다.", "file": updated})
