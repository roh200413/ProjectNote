from datetime import datetime, timezone
import uuid
from pathlib import Path
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods

from server.application.web_support import effective_user_profile, login_required_page, signature_repository
from server.domains.research_notes.models import ResearchNote, ResearchNoteFile, ResearchNoteFolder
from server.domains.research_notes.storage_paths import source_pdf_dir, source_images_dir, folder_relpath




def _build_storage_key(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    return f"{uuid.uuid4().hex}{suffix}" if suffix else uuid.uuid4().hex
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
    username = request.session.get("user_profile", {}).get("username", "")
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
    return redirect("/final-download")


@require_GET
@ensure_csrf_cookie
@login_required_page
def signature_page(request):
    return redirect("/signatures")


@require_GET
@ensure_csrf_cookie
@login_required_page
def my_page(request):
    return redirect("/my-page")


@require_http_methods(["POST"])
@login_required_page
def update_my_signature(request):
    signature_data_url = request.POST.get("signature_data_url", "")
    if not signature_data_url.startswith("data:image/"):
        return JsonResponse({"message": "유효한 이미지 데이터가 아닙니다."}, status=400)

    username = request.session.get("user_profile", {}).get("username", "")
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
    note = ResearchNote.objects.create(
        title=safe_name,
        owner=owner_name,
        project_code="",
        period=datetime.now(timezone.utc).strftime("%Y.%m.%d"),
        files=1,
        members=1,
        summary=f"업로드 파일: {safe_name}",
    )

    extension_guess = Path(safe_name).suffix.lstrip('.').lower()
    note_folder = source_pdf_dir(note) if extension_guess == 'pdf' else source_images_dir(note)
    note_folder.mkdir(parents=True, exist_ok=True)
    storage_key = _build_storage_key(safe_name)
    target_path = note_folder / storage_key
    with target_path.open("wb") as destination:
        for chunk in upload.chunks():
            destination.write(chunk)

    extension = target_path.suffix.lstrip(".").lower() or "bin"
    created_text = datetime.now(timezone.utc).strftime("%Y.%m.%d / %I:%M %p")
    ResearchNoteFile.objects.create(
        note=note,
        name=safe_name,
        original_name=safe_name,
        storage_key=storage_key,
        author=owner_name,
        format=extension,
        created=created_text,
    )
    ResearchNoteFolder.objects.create(note=note, name=folder_relpath(note_folder))

    return JsonResponse(
        {
            "message": "연구노트가 업로드되었습니다.",
            "note_id": str(note.id),
            "file_path": str(target_path),
        },
        status=201,
    )
