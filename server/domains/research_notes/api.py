import base64
import mimetypes
from datetime import datetime
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods
from pypdf import PageObject, PdfReader, PdfWriter, Transformation
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas

from .models import ResearchNote
from server.domains.admin.models import UserAccount
from server.application.web_support import login_required_page, research_note_repository, signature_repository


def _setup_korean_font() -> str | None:
    for font_name in ("HYGothic-Medium", "HYSMyeongJo-Medium"):
        try:
            pdfmetrics.getFont(font_name)
            return font_name
        except KeyError:
            try:
                pdfmetrics.registerFont(UnicodeCIDFont(font_name))
                return font_name
            except Exception:
                continue
    return None


KOREAN_PDF_FONT = _setup_korean_font()


def _set_pdf_font(pdf, size: int, bold: bool = False) -> None:
    if KOREAN_PDF_FONT:
        pdf.setFont(KOREAN_PDF_FONT, size)
        return
    pdf.setFont("Helvetica-Bold" if bold else "Helvetica", size)


def _research_note_pdf_cache_path(note_id: str, file_id: str) -> Path:
    return Path(settings.RESEARCH_NOTES_STORAGE_ROOT) / "_pdf_cache" / str(note_id) / f"{file_id}.pdf"


def _read_research_note_pdf_cache(note_id: str, file_id: str) -> bytes | None:
    cache_path = _research_note_pdf_cache_path(note_id, file_id)
    if cache_path.exists() and cache_path.is_file():
        try:
            return cache_path.read_bytes()
        except Exception:
            return None
    return None


def _write_research_note_pdf_cache(note_id: str, file_id: str, pdf_bytes: bytes) -> None:
    cache_path = _research_note_pdf_cache_path(note_id, file_id)
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(pdf_bytes)
    except Exception:
        return


def _invalidate_research_note_pdf_cache(note_id: str, file_id: str) -> None:
    cache_path = _research_note_pdf_cache_path(note_id, file_id)
    try:
        if cache_path.exists():
            cache_path.unlink()
    except Exception:
        return


@require_GET
def research_notes_api(_request):
    return JsonResponse(research_note_repository.list_research_notes(), safe=False)


@require_GET
def research_note_detail_api(_request, note_id: str):
    try:
        return JsonResponse(research_note_repository.get_research_note(note_id))
    except ResearchNote.DoesNotExist as exc:
        raise Http404("Research note not found") from exc


@require_GET
def research_note_files_api(_request, note_id: str):
    try:
        research_note_repository.get_research_note(note_id)
    except ResearchNote.DoesNotExist as exc:
        raise Http404("Research note not found") from exc

    files = research_note_repository.list_note_files(note_id)
    payload = [
        {
            **item,
            "content_url": f"/frontend/research-notes/{note_id}/files/{item['id']}/content",
            "download_url": f"/frontend/research-notes/{note_id}/files/{item['id']}/content?download=1",
        }
        for item in files
    ]
    return JsonResponse(payload, safe=False)


@require_GET
def research_note_folders_api(_request, note_id: str):
    try:
        research_note_repository.get_research_note(note_id)
    except ResearchNote.DoesNotExist as exc:
        raise Http404("Research note not found") from exc

    folders = research_note_repository.list_note_folders(note_id)
    payload = [
        {
            "id": str(index + 1),
            "name": str(Path(raw).name or raw),
            "raw_path": raw,
        }
        for index, raw in enumerate(folders)
    ]
    return JsonResponse(payload, safe=False)


@require_http_methods(["POST"])
def research_note_update_api(request, note_id: str):
    try:
        show_title_raw = request.POST.get("show_title")
        show_title = None if show_title_raw is None else str(show_title_raw).strip().lower() in {"1", "true", "on", "yes"}
        note = research_note_repository.update_research_note(note_id, request.POST.get("title"), request.POST.get("summary"), show_title=show_title)
    except ResearchNote.DoesNotExist as exc:
        raise Http404("Research note not found") from exc
    return JsonResponse({"message": "연구노트가 업데이트되었습니다.", "note": note})


@require_GET
@ensure_csrf_cookie
@login_required_page
def research_notes_page(request):
    return redirect("/research-notes")


@require_GET
@ensure_csrf_cookie
@login_required_page
def research_note_detail_page(request, note_id: str):
    return redirect(f"/research-notes/{note_id}")


def _build_research_note_viewer_context(note_id: str, requested_file: str | None = None) -> dict:
    note = research_note_repository.get_research_note(note_id)
    files = research_note_repository.list_note_files(note_id)
    if not files:
        raise Http404("Research note file not found")

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

    return {
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
        "show_title": bool(note.get("show_title", True)),
    }




@require_GET
def research_note_viewer_context_api(request, note_id: str):
    try:
        return JsonResponse(_build_research_note_viewer_context(note_id, request.GET.get("file")))
    except ResearchNote.DoesNotExist as exc:
        raise Http404("Research note not found") from exc


@require_GET
@ensure_csrf_cookie
@login_required_page
def research_note_cover_page(request, note_id: str):
    return redirect(f"/research-notes/{note_id}/cover")


@require_GET
@ensure_csrf_cookie
@login_required_page
def research_note_viewer_page(request, note_id: str):
    file_id = (request.GET.get("file") or "").strip()
    query = f"?file={file_id}" if file_id else ""
    return redirect(f"/research-notes/{note_id}/viewer{query}")


@require_GET
@ensure_csrf_cookie
@login_required_page
def research_note_printable_page(request, note_id: str):
    file_id = (request.GET.get("file") or "").strip()
    query = f"?file={file_id}" if file_id else ""
    return redirect(f"/research-notes/{note_id}/printable{query}")


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


@require_GET
@ensure_csrf_cookie
@login_required_page
def research_note_viewer_export_pdf_api(request, note_id: str):
    files = research_note_repository.list_note_files(note_id)
    if not files:
        raise Http404("Research note file not found")

    requested_file = request.GET.get("file")
    selected_file = files[0]
    if requested_file:
        matched = next((item for item in files if item["id"] == requested_file), None)
        if matched:
            selected_file = matched

    file_id = str(selected_file["id"])
    pdf_bytes = _read_research_note_pdf_cache(note_id, file_id)

    if pdf_bytes is None:
        try:
            pdf_bytes = build_research_note_file_pdf(note_id, file_id)
        except ResearchNote.DoesNotExist as exc:
            raise Http404("Research note not found") from exc
        _write_research_note_pdf_cache(note_id, file_id, pdf_bytes)

    filename = f"research_note_{note_id}_{Path(str(selected_file.get('name') or 'research_note')).stem}.pdf"
    return FileResponse(BytesIO(pdf_bytes), as_attachment=True, filename=filename, content_type="application/pdf")


def build_research_note_file_pdf(note_id: str, file_id: str) -> bytes:
    try:
        note = research_note_repository.get_research_note(note_id)
    except ResearchNote.DoesNotExist as exc:
        raise Http404("Research note not found") from exc

    files = research_note_repository.list_note_files(note_id)
    if not files:
        raise Http404("Research note file not found")

    selected_file = next((item for item in files if item["id"] == file_id), files[0])

    safe_name = Path(selected_file["name"]).name
    candidates = [Path(folder) / safe_name for folder in research_note_repository.list_note_folders(note_id)]
    if not candidates:
        storage_root = Path(settings.RESEARCH_NOTES_STORAGE_ROOT)
        candidates = list(storage_root.glob(f"*/{note_id}/{safe_name}"))

    source = next((c for c in candidates if c.exists() and c.is_file()), None)
    if not source:
        raise Http404("Research note file content not found")

    note_obj = ResearchNote.objects.select_related("project").filter(id=note_id).first()
    manager_raw = (note_obj.project.manager if note_obj and note_obj.project else "") if note_obj else ""

    author_name = str(selected_file.get("author") or "-")
    created_text = str(selected_file.get("created") or "-")
    show_title = bool(note.get("show_title", True))

    author_user = UserAccount.objects.filter(username=author_name).first() or UserAccount.objects.filter(display_name=author_name).first()
    manager_user = UserAccount.objects.filter(username=manager_raw).first() or UserAccount.objects.filter(display_name=manager_raw).first()

    manager_name = manager_user.display_name if manager_user else manager_raw
    reviewer_date = datetime.now().strftime("%Y.%m.%d / %I:%M %p")
    author_signature_data_url = signature_repository.read_signature(author_user.username).get("signature_data_url", "") if author_user else ""
    manager_signature_data_url = signature_repository.read_signature(manager_user.username).get("signature_data_url", "") if manager_user else ""

    def _image_reader_from_data_url(data_url: str):
        raw = str(data_url or "")
        if not raw.startswith("data:image") or "," not in raw:
            return None
        try:
            encoded = raw.split(",", 1)[1]
            return ImageReader(BytesIO(base64.b64decode(encoded)))
        except Exception:
            return None

    def _draw_signature_panel(pdf, left: float, bottom: float, width: float, *, compact: bool = False):
        col = width / 4
        box_h = 56 if compact else 64

        for idx in range(4):
            x = left + idx * col
            pdf.rect(x, bottom, col, box_h)
        for idx in (0, 2):
            x = left + idx * col
            pdf.line(x, bottom + box_h / 2, x + col, bottom + box_h / 2)

        _set_pdf_font(pdf, 7 if compact else 8)
        pdf.drawString(left + 4, bottom + box_h - 10, "작성자")
        pdf.drawString(left + 4, bottom + (box_h / 2) - 10, "작성 일자")
        _set_pdf_font(pdf, 9 if compact else 10)
        pdf.drawCentredString(left + col / 2, bottom + (box_h / 2) + 4, author_name)
        pdf.drawCentredString(left + col / 2, bottom + 8, created_text)

        x2 = left + col
        _set_pdf_font(pdf, 7 if compact else 8)
        pdf.drawString(x2 + 4, bottom + box_h - 10, "사인")
        author_reader = _image_reader_from_data_url(author_signature_data_url)
        if author_reader:
            pdf.drawImage(author_reader, x2 + 10, bottom + 6, width=col - 20, height=(box_h - 20), preserveAspectRatio=True, anchor='c')
        else:
            _set_pdf_font(pdf, 8 if compact else 9)
            pdf.drawCentredString(x2 + col / 2, bottom + (box_h / 2) - 2, "사인 없음")

        x3 = left + (col * 2)
        _set_pdf_font(pdf, 7 if compact else 8)
        pdf.drawString(x3 + 4, bottom + box_h - 10, "점검자")
        pdf.drawString(x3 + 4, bottom + (box_h / 2) - 10, "점검 일자")
        _set_pdf_font(pdf, 9 if compact else 10)
        pdf.drawCentredString(x3 + col / 2, bottom + (box_h / 2) + 4, manager_name or "-")
        pdf.drawCentredString(x3 + col / 2, bottom + 8, reviewer_date)

        x4 = left + (col * 3)
        _set_pdf_font(pdf, 7 if compact else 8)
        pdf.drawString(x4 + 4, bottom + box_h - 10, "점검자 사인")
        manager_reader = _image_reader_from_data_url(manager_signature_data_url)
        if manager_reader:
            pdf.drawImage(manager_reader, x4 + 10, bottom + 6, width=col - 20, height=(box_h - 20), preserveAspectRatio=True, anchor='c')
        else:
            _set_pdf_font(pdf, 8 if compact else 9)
            pdf.drawCentredString(x4 + col / 2, bottom + (box_h / 2) - 2, "사인 없음")

    def _sheet_layout():
        return {
            "sheet_left": 34,
            "sheet_bottom": 42,
            "sheet_width": pw - 68,
            "sheet_height": ph - 84,
            "content_bottom": 134,
            "content_top": ph - 84,
        }

    def _build_sheet_overlay_pdf() -> PdfReader:
        layout = _sheet_layout()
        overlay_buffer = BytesIO()
        pdf = canvas.Canvas(overlay_buffer, pagesize=A4)

        pdf.roundRect(layout["sheet_left"], layout["sheet_bottom"], layout["sheet_width"], layout["sheet_height"], 8, stroke=1, fill=0)

        header_top = layout["sheet_bottom"] + layout["sheet_height"] - 24
        if show_title:
            _set_pdf_font(pdf, 10, bold=True)
            pdf.drawString(layout["sheet_left"] + 16, header_top, str(note.get("title") or "연구노트"))
        pdf.line(layout["sheet_left"] + 16, header_top - 6, layout["sheet_left"] + layout["sheet_width"] - 16, header_top - 6)

        content_left = layout["sheet_left"] + 16
        content_bottom = layout["content_bottom"]
        content_width = layout["sheet_width"] - 32
        content_height = layout["content_top"] - layout["content_bottom"]
        pdf.roundRect(content_left, content_bottom, content_width, content_height, 4, stroke=1, fill=0)

        _draw_signature_panel(pdf, left=content_left, bottom=layout["sheet_bottom"] + 24, width=content_width, compact=True)
        pdf.save()
        overlay_buffer.seek(0)
        return PdfReader(overlay_buffer, strict=False)

    writer = PdfWriter()
    fmt = str(selected_file.get("format", "")).lower()

    pw, ph = A4
    if fmt == "pdf":
        with source.open("rb") as src:
            reader = PdfReader(src, strict=False)
            if getattr(reader, "is_encrypted", False):
                try:
                    reader.decrypt("")
                except Exception:
                    pass

            if reader.pages:
                layout = _sheet_layout()
                content_left = layout["sheet_left"] + 16
                content_bottom = layout["content_bottom"]
                content_width = layout["sheet_width"] - 32
                content_height = layout["content_top"] - layout["content_bottom"]
                overlay_page = _build_sheet_overlay_pdf().pages[0]

                for page in reader.pages:
                    src_w = float(page.mediabox.width)
                    src_h = float(page.mediabox.height)
                    if src_w <= 0 or src_h <= 0:
                        continue

                    scale = min(content_width / src_w, content_height / src_h)
                    tx = content_left + (content_width - (src_w * scale)) / 2
                    ty = content_bottom + (content_height - (src_h * scale)) / 2

                    rebuilt = PageObject.create_blank_page(width=pw, height=ph)
                    rebuilt.merge_transformed_page(page, Transformation().scale(scale, scale).translate(tx, ty))
                    rebuilt.merge_page(overlay_page)
                    writer.add_page(rebuilt)
    else:
        page_buffer = BytesIO()
        pdf = canvas.Canvas(page_buffer, pagesize=A4)

        layout = _sheet_layout()
        sheet_left = layout["sheet_left"]
        sheet_bottom = layout["sheet_bottom"]
        sheet_width = layout["sheet_width"]
        sheet_height = layout["sheet_height"]
        content_left = sheet_left + 16
        content_bottom = layout["content_bottom"]
        content_width = sheet_width - 32
        content_height = layout["content_top"] - layout["content_bottom"]

        pdf.roundRect(sheet_left, sheet_bottom, sheet_width, sheet_height, 8, stroke=1, fill=0)

        header_top = sheet_bottom + sheet_height - 24
        if show_title:
            _set_pdf_font(pdf, 10, bold=True)
            pdf.drawString(sheet_left + 16, header_top, str(note.get("title") or "연구노트"))
        pdf.line(sheet_left + 16, header_top - 6, sheet_left + sheet_width - 16, header_top - 6)
        pdf.roundRect(content_left, content_bottom, content_width, content_height, 4, stroke=1, fill=0)

        image_exts = {"png", "jpg", "jpeg", "webp", "svg", "heic", "heif"}
        if fmt in image_exts:
            try:
                pdf.drawImage(
                    str(source),
                    content_left,
                    content_bottom,
                    width=content_width,
                    height=content_height,
                    preserveAspectRatio=True,
                    anchor="c",
                )
            except Exception:
                _set_pdf_font(pdf, 10)
                pdf.drawString(content_left + 12, content_bottom + content_height - 24, "이미지를 불러오지 못했습니다. 원본파일을 확인해주세요.")
        else:
            _set_pdf_font(pdf, 11)
            pdf.drawString(content_left + 12, content_bottom + content_height - 24, f"파일명: {selected_file.get('name', '-')}")
            _set_pdf_font(pdf, 10)
            pdf.drawString(content_left + 12, content_bottom + content_height - 42, f"형식: {fmt.upper() if fmt else '-'}")
            pdf.drawString(content_left + 12, content_bottom + content_height - 60, "해당 파일 형식은 미리보기를 지원하지 않습니다.")

        _draw_signature_panel(pdf, left=content_left, bottom=sheet_bottom + 24, width=content_width, compact=True)

        pdf.showPage()
        pdf.save()
        page_buffer.seek(0)
        writer.append(PdfReader(page_buffer, strict=False))

    output = BytesIO()
    writer.write(output)
    return output.getvalue()




@require_http_methods(["POST"])
def research_note_file_upload_api(request, note_id: str):
    try:
        note_obj = ResearchNote.objects.select_related("project").get(id=note_id)
    except ResearchNote.DoesNotExist as exc:
        raise Http404("Research note not found") from exc

    upload = request.FILES.get("file") or request.FILES.get("research_note_file")
    if not upload:
        return JsonResponse({"detail": "업로드할 파일이 없습니다."}, status=400)

    safe_name = Path(upload.name).name
    extension = Path(safe_name).suffix.lstrip(".").lower()
    allowed_extensions = {"jpeg", "jpg", "png", "svg", "tiff", "webp", "heif", "heic", "pdf"}
    if extension not in allowed_extensions:
        return JsonResponse({"detail": "PDF 또는 이미지 파일만 업로드할 수 있습니다."}, status=400)

    profile = effective_user_profile(request) or {}
    username = str(profile.get("username") or "anonymous").strip() or "anonymous"
    author_name = str(profile.get("name") or username).strip() or username

    existing_folders = research_note_repository.list_note_folders(note_id)
    if existing_folders:
        note_folder = Path(existing_folders[0])
    else:
        note_folder = Path(settings.RESEARCH_NOTES_STORAGE_ROOT) / username / str(note_id)

    note_folder.mkdir(parents=True, exist_ok=True)
    target_path = note_folder / safe_name
    with target_path.open("wb") as destination:
        for chunk in upload.chunks():
            destination.write(chunk)

    file_obj = ResearchNoteFile.objects.create(
        note=note_obj,
        name=safe_name,
        author=author_name,
        format=extension,
        created=datetime.now().strftime("%Y.%m.%d / %I:%M %p"),
    )

    ResearchNoteFolder.objects.get_or_create(note=note_obj, name=str(note_folder))
    note_obj.files = note_obj.note_files.count()
    note_obj.save(update_fields=["files", "last_updated_at", "updated_at"])

    payload = {
        "id": str(file_obj.id),
        "name": file_obj.name,
        "author": file_obj.author,
        "format": file_obj.format,
        "created": file_obj.created,
        "content_url": f"/frontend/research-notes/{note_id}/files/{file_obj.id}/content",
        "download_url": f"/frontend/research-notes/{note_id}/files/{file_obj.id}/content?download=1",
    }
    return JsonResponse({"message": "연구파일이 업로드되었습니다.", "file": payload}, status=201)

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
    _invalidate_research_note_pdf_cache(note_id, file_id)
    return JsonResponse({"message": "파일 정보가 업데이트되었습니다.", "file": updated})
