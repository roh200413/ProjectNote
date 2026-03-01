from datetime import datetime, timezone
from pathlib import Path
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods

from server.application.web_support import effective_user_profile, login_required_page, page_context, signature_repository
from server.domains.research_notes.models import ResearchNote, ResearchNoteFile, ResearchNoteFolder


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
    username = (effective_user_profile(request) or {}).get("username", "")
    if not username:
        return JsonResponse({"detail": "로그인이 필요합니다."}, status=401)
    if request.method == "GET":
        return JsonResponse(signature_repository.read_signature(username))
    payload = signature_repository.update_signature(
        username=username,
        status=request.POST.get("status", "valid"),
        signature_data_url=request.POST.get("signature_data_url", ""),
    )
    return JsonResponse(payload)


@require_GET
@ensure_csrf_cookie
@login_required_page
def final_download_page(request):
    return render(
        request,
        "workflow/final_download.html",
        page_context(request, {"report_name": "projectnote-final-report.pdf"}),
    )


@require_GET
@ensure_csrf_cookie
@login_required_page
def signature_page(request):
    username = (effective_user_profile(request) or {}).get("username", "")
    return render(request, "workflow/signatures.html", page_context(request, {"signature": signature_repository.read_signature(username)}))


@require_GET
@ensure_csrf_cookie
@login_required_page
def my_page(request):
    profile = (effective_user_profile(request) or {}).copy()
    username = profile.get("username", "")
    profile["signature"] = signature_repository.read_signature(username).get("signature_data_url", "") if username else ""
    return render(request, "workflow/my_page.html", page_context(request, {"profile": profile}))


@require_http_methods(["POST"])
@login_required_page
def update_my_signature(request):
    signature_data_url = request.POST.get("signature_data_url", "")
    if not signature_data_url.startswith("data:image/"):
        return JsonResponse({"message": "유효한 이미지 데이터가 아닙니다."}, status=400)

    username = (effective_user_profile(request) or {}).get("username", "")
    if not username:
        return JsonResponse({"message": "로그인이 필요합니다."}, status=401)
    signature_repository.update_signature(username=username, signature_data_url=signature_data_url)
    return JsonResponse({"message": "서명이 업데이트되었습니다."})


@require_http_methods(["POST"])
@login_required_page
def upload_my_research_note(request):
    profile = effective_user_profile(request) or {}
    username = str(profile.get("username", "")).strip()
    if not username:
        return JsonResponse({"message": "로그인이 필요합니다."}, status=401)

    upload = request.FILES.get("research_note_file")
    if not upload:
        return JsonResponse({"message": "업로드할 파일이 없습니다."}, status=400)

    safe_name = Path(upload.name).name
    if not safe_name:
        return JsonResponse({"message": "유효한 파일명이 필요합니다."}, status=400)

    owner_name = str(profile.get("name", username)).strip() or username
    storage_root = Path(settings.RESEARCH_NOTES_STORAGE_ROOT)
    note = ResearchNote.objects.create(
        title=safe_name,
        owner=owner_name,
        project_code="",
        period=datetime.now(timezone.utc).strftime("%Y.%m.%d"),
        files=1,
        members=1,
        summary=f"업로드 파일: {safe_name}",
    )

    note_folder = storage_root / username / str(note.id)
    note_folder.mkdir(parents=True, exist_ok=True)
    target_path = note_folder / safe_name
    with target_path.open("wb") as destination:
        for chunk in upload.chunks():
            destination.write(chunk)

    extension = target_path.suffix.lstrip(".").lower() or "bin"
    created_text = datetime.now(timezone.utc).strftime("%Y.%m.%d / %I:%M %p")
    ResearchNoteFile.objects.create(
        note=note,
        name=safe_name,
        author=owner_name,
        format=extension,
        created=created_text,
    )
    ResearchNoteFolder.objects.create(note=note, name=str(note_folder))

    return JsonResponse(
        {
            "message": "연구노트가 업로드되었습니다.",
            "note_id": str(note.id),
            "file_path": str(target_path),
        },
        status=201,
    )
