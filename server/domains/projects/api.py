import base64
import json
import uuid
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.db import OperationalError, ProgrammingError
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

from .models import Project, ProjectMember, ProjectNoteCover
from server.domains.admin.models import UserAccount
from server.domains.research_notes.models import ResearchNote, ResearchNoteFile, ResearchNoteFolder
from server.domains.research_notes.api import (
    build_research_note_file_pdf,
    _read_research_note_pdf_cache,
    _write_research_note_pdf_cache,
)
from server.application.web_support import (
    json_uuid_validation_error,
    login_required_page,
    effective_user_profile,
    project_repository,
    project_service,
    admin_repository,
    research_note_repository,
    signature_repository,
    dashboard_counts,
)


def _manager_options_for_team(team_id: int | None) -> list[dict]:
    users = UserAccount.objects.filter(is_approved=True, role__in=[UserAccount.Role.OWNER, UserAccount.Role.ADMIN])
    if team_id is not None:
        users = users.filter(team_id=team_id)
    users = users.order_by("display_name")
    return [{"username": user.username, "display_name": user.display_name} for user in users]


def _cover_to_dict(cover: ProjectNoteCover, project: Project, manager_display: str) -> dict:
    return {
        "title": cover.title or project.name,
        "code": cover.code or project.code,
        "business_name": cover.business_name or project.business_name,
        "organization": cover.organization or project.organization,
        "manager": cover.manager or manager_display,
        "start_date": cover.start_date.isoformat() if cover.start_date else (project.start_date.isoformat() if project.start_date else ""),
        "end_date": cover.end_date.isoformat() if cover.end_date else (project.end_date.isoformat() if project.end_date else ""),
        "show_business_name": cover.show_business_name,
        "show_title": cover.show_title,
        "show_code": cover.show_code,
        "show_org": cover.show_org,
        "show_manager": cover.show_manager,
        "show_period": cover.show_period,
        "cover_image_data_url": cover.cover_image_data_url or "",
    }


def _default_cover_data(project: dict, manager_display: str) -> dict:
    return {
        "title": project.get("name") or "",
        "code": project.get("code") or "",
        "business_name": project.get("business_name") or "",
        "organization": project.get("organization") or "",
        "manager": manager_display or project.get("manager") or "",
        "start_date": project.get("start_date") or "",
        "end_date": project.get("end_date") or "",
        "show_business_name": True,
        "show_title": True,
        "show_code": True,
        "show_org": True,
        "show_manager": True,
        "show_period": True,
        "cover_image_data_url": "",
    }


def _load_cover_data(project_obj: Project, project: dict, manager_display: str) -> dict:
    try:
        cover, _ = ProjectNoteCover.objects.get_or_create(
            project=project_obj,
            defaults={
                "title": project_obj.name,
                "code": project_obj.code,
                "business_name": project_obj.business_name,
                "organization": project_obj.organization,
                "manager": manager_display,
                "start_date": project_obj.start_date,
                "end_date": project_obj.end_date,
            },
        )
        return _cover_to_dict(cover, project_obj, manager_display)
    except (OperationalError, ProgrammingError):
        return _default_cover_data(project, manager_display)




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

def _decode_data_url(data_url: str):
    raw = str(data_url or "")
    if not raw.startswith("data:") or "," not in raw:
        return "", b""
    header, encoded = raw.split(",", 1)
    mime = header[5:].split(";", 1)[0].lower()
    try:
        return mime, base64.b64decode(encoded)
    except Exception:
        return "", b""


def _project_cover_pdf_cache_path(project_id: str) -> Path:
    return Path(settings.RESEARCH_NOTES_STORAGE_ROOT) / "_pdf_cache" / "project_covers" / f"{project_id}.pdf"


def _read_project_cover_pdf_cache(project_id: str) -> bytes | None:
    cache_path = _project_cover_pdf_cache_path(project_id)
    if cache_path.exists() and cache_path.is_file():
        try:
            return cache_path.read_bytes()
        except Exception:
            return None
    return None


def _write_project_cover_pdf_cache(project_id: str, pdf_bytes: bytes) -> None:
    cache_path = _project_cover_pdf_cache_path(project_id)
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(pdf_bytes)
    except Exception:
        return


def _invalidate_project_cover_pdf_cache(project_id: str) -> None:
    cache_path = _project_cover_pdf_cache_path(project_id)
    try:
        if cache_path.exists():
            cache_path.unlink()
    except Exception:
        return


def _build_project_cover_pdf_bytes(profile: dict, project_id: str, cover_data: dict) -> bytes:
    cover_image_data_url = str(cover_data.get("cover_image_data_url") or "")
    cover_mime, cover_payload = _decode_data_url(cover_image_data_url)

    if cover_mime == "application/pdf" and cover_payload:
        return cover_payload

    cover_buffer = BytesIO()
    c = canvas.Canvas(cover_buffer, pagesize=A4)
    w, h = A4

    drew_cover_image = False
    if cover_mime.startswith("image/") and cover_payload:
        try:
            img_reader = ImageReader(BytesIO(cover_payload))
            c.drawImage(img_reader, 0, 0, width=w, height=h, preserveAspectRatio=False)
            drew_cover_image = True
        except Exception:
            drew_cover_image = False

    _set_pdf_font(c, 16, bold=True)
    c.drawCentredString(w / 2, h - 80, "Electronic Lab Notebook")
    if not drew_cover_image:
        _set_pdf_font(c, 26, bold=True)
        c.drawCentredString(w / 2, h - 130, "연구노트")
    if cover_data.get("show_title"):
        _set_pdf_font(c, 22, bold=True)
        c.drawCentredString(w / 2, h - 170, str(cover_data.get("title") or ""))

    lines = []
    if cover_data.get("show_business_name"):
        lines.append(("사업명", str(cover_data.get("business_name") or "-")))
    if cover_data.get("show_code"):
        lines.append(("과제 번호", str(cover_data.get("code") or "-")))
    if cover_data.get("show_org"):
        lines.append(("담당 기관", str(cover_data.get("organization") or "-")))
    if cover_data.get("show_manager"):
        lines.append(("작업자", str(cover_data.get("manager") or "-")))
    if cover_data.get("show_period"):
        start_text = str(cover_data.get("start_date") or "").strip()
        end_text = str(cover_data.get("end_date") or "").strip()
        period = f"{start_text} ~ {end_text}" if start_text and end_text else (start_text or end_text or "-")
        lines.append(("기간", period))

    # 편집기 미리보기와 동일하게 표지 이미지를 사용해도 메타 정보를 함께 출력한다.
    y = h - 240
    _set_pdf_font(c, 12)
    for label, value in lines:
        c.drawString(70, y, f"{label}:")
        c.drawString(150, y, value)
        y -= 24

    footer_company = str((profile.get("team") or profile.get("organization") or "미지정"))
    _set_pdf_font(c, 11)
    c.drawCentredString(w / 2, 60, f"ProjectNote - {footer_company}")

    c.showPage()
    c.save()
    cover_buffer.seek(0)
    return cover_buffer.getvalue()


def _get_or_build_project_cover_pdf_bytes(profile: dict, project_id: str, cover_data: dict) -> bytes:
    cached = _read_project_cover_pdf_cache(project_id)
    if cached is not None:
        return cached
    pdf_bytes = _build_project_cover_pdf_bytes(profile, project_id, cover_data)
    _write_project_cover_pdf_cache(project_id, pdf_bytes)
    return pdf_bytes


@require_GET
def projects(request):
    org_id = request.GET.get("org_id")
    if org_id:
        try:
            uuid.UUID(org_id)
        except ValueError:
            return json_uuid_validation_error("org_id", org_id)
    profile = effective_user_profile(request) or {}
    return JsonResponse(project_repository.visible_projects_for_user(profile), safe=False)


@require_http_methods(["GET", "POST"])
def project_management_api(request):
    if request.method == "GET":
        profile = effective_user_profile(request) or {}
        return JsonResponse(project_repository.visible_projects_for_user(profile), safe=False)
    payload = request.POST.copy()
    team_id = request.session.get("user_profile", {}).get("team_id")
    if team_id:
        payload["company_id"] = str(team_id)
    project = project_service.create_project(payload, request.session.get("user_profile", {}))
    return JsonResponse(project, status=201)


@require_GET
def project_detail_api(request, project_id: str):
    profile = effective_user_profile(request) or {}
    if not project_repository.can_view_project(project_id, profile):
        return JsonResponse({"detail": "권한이 없습니다."}, status=403)

    try:
        project = project_repository.project_to_dict(Project.objects.get(id=project_id))
    except Project.DoesNotExist:
        return JsonResponse({"detail": "프로젝트를 찾을 수 없습니다."}, status=404)

    return JsonResponse(project)


@require_GET
@ensure_csrf_cookie
@login_required_page
def project_management_page(request):
    return redirect("/projects")


@require_GET
@ensure_csrf_cookie
@login_required_page
def project_create_page(request):
    return redirect("/projects/create")


@require_GET
@ensure_csrf_cookie
@login_required_page
def project_detail_page(request, project_id: str):
    return redirect(f"/projects/{project_id}")


@require_GET
@ensure_csrf_cookie
@login_required_page
def project_researchers_page(request, project_id: str):
    return redirect(f"/projects/{project_id}/researchers")


@require_GET
@ensure_csrf_cookie
@login_required_page
def project_research_notes_page(request, project_id: str):
    return redirect(f"/projects/{project_id}/research-notes")


@require_GET
def project_research_notes_api(request, project_id: str):
    profile = effective_user_profile(request) or {}
    if not project_repository.can_view_project(project_id, profile):
        return JsonResponse({"detail": "권한이 없습니다."}, status=403)

    try:
        Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return JsonResponse({"detail": "프로젝트를 찾을 수 없습니다."}, status=404)

    note_ids = set(project_repository.project_note_ids(project_id))
    notes = [note for note in research_note_repository.list_research_notes() if note["id"] in note_ids]
    return JsonResponse(notes, safe=False)


@require_GET
@ensure_csrf_cookie
@login_required_page
def project_research_notes_print_page(request, project_id: str):
    selected = request.GET.urlencode()
    query = f"?{selected}" if selected else ""
    return redirect(f"/projects/{project_id}/research-notes/print{query}")


@require_http_methods(["GET", "POST"])
def project_research_notes_export_pdf_api(request, project_id: str):
    profile = effective_user_profile(request) or {}
    if not project_repository.can_view_project(project_id, profile):
        return JsonResponse({"detail": "권한이 없습니다."}, status=403)

    project_obj = Project.objects.filter(id=project_id).first()
    if not project_obj:
        return JsonResponse({"detail": "프로젝트를 찾을 수 없습니다."}, status=404)

    if request.method == "POST":
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except Exception:
            return JsonResponse({"detail": "잘못된 요청 형식입니다."}, status=400)

        page_images = payload.get("page_images", [])
        if not isinstance(page_images, list) or not page_images:
            return JsonResponse({"detail": "내보낼 페이지 이미지가 없습니다."}, status=400)

        writer = PdfWriter()

        for image_data in page_images:
            raw = str(image_data or "")
            if not raw.startswith("data:image") or "," not in raw:
                continue
            try:
                encoded = raw.split(",", 1)[1]
                reader = ImageReader(BytesIO(base64.b64decode(encoded)))
            except Exception:
                continue

            try:
                iw, ih = reader.getSize()
                iw = float(iw)
                ih = float(ih)
            except Exception:
                continue
            if iw <= 0 or ih <= 0:
                continue

            page_buffer = BytesIO()
            pdf = canvas.Canvas(page_buffer, pagesize=(iw, ih))
            # 화면 캡처 비율을 그대로 유지해 삽입
            pdf.drawImage(reader, 0, 0, width=iw, height=ih, preserveAspectRatio=False)
            pdf.showPage()
            pdf.save()
            page_buffer.seek(0)
            writer.append(PdfReader(page_buffer, strict=False))

        if not writer.pages:
            return JsonResponse({"detail": "유효한 페이지 이미지가 없습니다."}, status=400)

        output = BytesIO()
        writer.write(output)
        output.seek(0)
        filename = f"project_{project_id}_research_notes_viewer_snapshot.pdf"
        return FileResponse(output, as_attachment=True, filename=filename, content_type="application/pdf")

    project = project_repository.project_to_dict(project_obj)
    manager_display = project.get("manager", "-")
    cover_data = _load_cover_data(project_obj, project, manager_display)

    # 1) 표지 PDF는 저장된 결과를 우선 사용
    cover_pdf_bytes = _get_or_build_project_cover_pdf_bytes(profile, project_id, cover_data)

    # 2) PDF 단순 병합 (표지 + 각 연구파일을 순서대로)
    writer = PdfWriter()
    writer.append(PdfReader(BytesIO(cover_pdf_bytes), strict=False))

    note_ids = project_repository.project_note_ids(project_id)
    all_notes = research_note_repository.list_research_notes()
    project_notes = [note for note in all_notes if note["id"] in note_ids]

    selected_pairs = set()
    for raw in request.GET.getlist("selected_file"):
        token = str(raw or "").strip()
        if ":" not in token:
            continue
        note_id, file_id = token.split(":", 1)
        note_id = note_id.strip()
        file_id = file_id.strip()
        if note_id and file_id:
            selected_pairs.add((note_id, file_id))

    merged_files = 0
    total_files = 0

    for note in project_notes:
        for file in research_note_repository.list_note_files(note["id"]):
            file_id = str(file.get("id") or "").strip()
            note_id = str(note["id"])
            if selected_pairs and (note_id, file_id) not in selected_pairs:
                continue

            total_files += 1
            try:
                file_pdf_bytes = _read_research_note_pdf_cache(note_id, file_id)
                if file_pdf_bytes is None:
                    file_pdf_bytes = build_research_note_file_pdf(note_id, file_id)
                    _write_research_note_pdf_cache(note_id, file_id, file_pdf_bytes)
                writer.append(PdfReader(BytesIO(file_pdf_bytes), strict=False))
                merged_files += 1
            except Exception:
                continue

    output = BytesIO()
    writer.write(output)
    output.seek(0)
    filename = f"project_{project_id}_research_notes.pdf"
    response = FileResponse(output, as_attachment=True, filename=filename, content_type="application/pdf")
    response["X-Merged-File-Count"] = str(merged_files)
    response["X-Total-File-Count"] = str(total_files)
    return response


@require_http_methods(["POST"])
def project_upload_research_note_api(request, project_id: str):
    profile = effective_user_profile(request) or {}
    if not project_repository.can_view_project(project_id, profile):
        return JsonResponse({"detail": "권한이 없습니다."}, status=403)

    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return JsonResponse({"detail": "프로젝트를 찾을 수 없습니다."}, status=404)

    uploads = request.FILES.getlist("research_note_file")
    if not uploads:
        single = request.FILES.get("research_note_file")
        if single:
            uploads = [single]
    if not uploads:
        return JsonResponse({"message": "업로드할 파일이 없습니다."}, status=400)

    allowed_extensions = {
        "jpeg", "jpg", "png", "svg", "tiff", "webp", "heif", "heic", "doc", "docx", "pptx", "ppt", "xls", "xlsx", "pdf"
    }
    for upload in uploads:
        ext = Path(Path(upload.name).name).suffix.lstrip(".").lower()
        if ext not in allowed_extensions:
            return JsonResponse({"message": "지원하지 않는 파일 형식입니다."}, status=400)

    owner_name = str(profile.get("name") or profile.get("username") or "미지정").strip() or "미지정"
    title = str(request.POST.get("title", "")).strip()
    summary = str(request.POST.get("summary", "")).strip()
    author = str(request.POST.get("author", owner_name)).strip() or owner_name

    now = datetime.now(timezone.utc)

    def _display_datetime(value: str | None) -> str:
        raw = str(value or "").strip()
        if not raw:
            return now.strftime("%Y.%m.%d / %I:%M %p")
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError:
            return now.strftime("%Y.%m.%d / %I:%M %p")
        return parsed.strftime("%Y.%m.%d / %I:%M %p")

    created_text = _display_datetime(request.POST.get("created_at"))
    updated_text = _display_datetime(request.POST.get("updated_at"))

    note_title = title or Path(Path(uploads[0].name).name).name
    note = ResearchNote.objects.create(
        project=project,
        title=note_title,
        owner=owner_name,
        project_code=project.code,
        period=updated_text,
        files=0,
        members=1,
        summary=summary,
    )

    username = str(profile.get("username") or "anonymous").strip() or "anonymous"
    storage_root = Path(settings.RESEARCH_NOTES_STORAGE_ROOT)
    note_folder = storage_root / username / str(note.id)
    note_folder.mkdir(parents=True, exist_ok=True)
    ResearchNoteFolder.objects.create(note=note, name=str(note_folder))

    created_count = 0
    for upload in uploads:
        safe_name = Path(upload.name).name
        stem = Path(safe_name).stem
        extension = Path(safe_name).suffix.lstrip(".").lower()

        if extension == "pdf":
            pdf_bytes = upload.read()
            split_success = False
            try:
                reader = PdfReader(BytesIO(pdf_bytes))
                for page_index, page in enumerate(reader.pages, start=1):
                    page_name = f"{stem}_p{page_index:03d}.pdf"
                    page_path = note_folder / page_name
                    writer = PdfWriter()
                    writer.add_page(page)
                    with page_path.open("wb") as destination:
                        writer.write(destination)
                    ResearchNoteFile.objects.create(
                        note=note,
                        name=page_name,
                        author=author,
                        format="pdf",
                        created=created_text,
                    )
                    created_count += 1
                split_success = len(reader.pages) > 0
            except Exception:
                split_success = False

            if split_success:
                continue

            fallback_path = note_folder / safe_name
            with fallback_path.open("wb") as destination:
                destination.write(pdf_bytes)
            ResearchNoteFile.objects.create(
                note=note,
                name=safe_name,
                author=author,
                format=extension,
                created=created_text,
            )
            created_count += 1
            continue

        target_path = note_folder / safe_name
        with target_path.open("wb") as destination:
            for chunk in upload.chunks():
                destination.write(chunk)
        ResearchNoteFile.objects.create(
            note=note,
            name=safe_name,
            author=author,
            format=extension,
            created=created_text,
        )
        created_count += 1

    note.files = created_count
    note.save(update_fields=["files", "period", "summary", "updated_at", "last_updated_at"])

    return JsonResponse({
        "message": "연구파일이 등록되었습니다.",
        "note_id": str(note.id),
        "created_files": created_count,
    }, status=201)


@require_GET
def project_cover_print_api(request, project_id: str):
    profile = effective_user_profile(request) or {}
    if not project_repository.can_view_project(project_id, profile):
        return JsonResponse({"detail": "권한이 없습니다."}, status=403)

    project_obj = Project.objects.filter(id=project_id).first()
    if not project_obj:
        return JsonResponse({"detail": "프로젝트를 찾을 수 없습니다."}, status=404)

    project = project_repository.project_to_dict(project_obj)
    manager_display = project.get("manager", "-")
    cover_data = _load_cover_data(project_obj, project, manager_display)

    pdf_bytes = _get_or_build_project_cover_pdf_bytes(profile, project_id, cover_data)
    return FileResponse(BytesIO(pdf_bytes), as_attachment=True, filename=f"project_{project_id}_cover.pdf", content_type="application/pdf")


@require_http_methods(["POST"])
def project_update_api(request, project_id: str):
    payload = request.POST.copy()
    try:
        updated = project_repository.update_project(project_id, {
            "name": payload.get("name", ""),
            "manager": payload.get("manager", ""),
            "business_name": payload.get("business_name", ""),
            "organization": payload.get("organization", ""),
            "code": payload.get("code", ""),
            "description": payload.get("description", ""),
            "start_date": payload.get("start_date", ""),
            "end_date": payload.get("end_date", ""),
            "status": payload.get("status", "draft"),
        })
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=404)
    return JsonResponse(updated)


@require_http_methods(["GET", "POST"])
def project_cover_update_api(request, project_id: str):
    profile = effective_user_profile(request) or {}

    if request.method == "GET":
        if not project_repository.can_view_project(project_id, profile):
            return JsonResponse({"detail": "권한이 없습니다."}, status=403)
        project_obj = Project.objects.filter(id=project_id).first()
        if not project_obj:
            return JsonResponse({"detail": "프로젝트를 찾을 수 없습니다."}, status=404)
        project = project_repository.project_to_dict(project_obj)
        manager_display = project.get("manager", "-")
        return JsonResponse(_load_cover_data(project_obj, project, manager_display))

    if not project_repository.can_manage_project_members(project_id, profile):
        return JsonResponse({"detail": "권한이 없습니다."}, status=403)
    project = Project.objects.filter(id=project_id).first()
    if not project:
        return JsonResponse({"detail": "프로젝트를 찾을 수 없습니다."}, status=404)

    try:
        cover, _ = ProjectNoteCover.objects.get_or_create(project=project)
    except (OperationalError, ProgrammingError):
        return JsonResponse({"detail": "DB 스키마가 최신이 아닙니다. python manage.py migrate 를 먼저 실행해주세요."}, status=409)

    def _as_bool(key: str, default: bool) -> bool:
        raw = str(request.POST.get(key, "")).strip().lower()
        if raw in {"1", "true", "on", "yes"}:
            return True
        if raw in {"0", "false", "off", "no"}:
            return False
        return default

    def _as_date(key: str):
        raw = str(request.POST.get(key, "")).strip()
        if not raw:
            return None
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            return None

    cover.title = str(request.POST.get("title", project.name)).strip()
    cover.code = str(request.POST.get("code", project.code)).strip()
    cover.business_name = str(request.POST.get("business_name", project.business_name)).strip()
    cover.organization = str(request.POST.get("organization", project.organization)).strip()
    cover.manager = str(request.POST.get("manager", project.manager)).strip()
    cover.start_date = _as_date("start_date")
    cover.end_date = _as_date("end_date")
    cover.show_business_name = _as_bool("show_business_name", True)
    cover.show_title = _as_bool("show_title", True)
    cover.show_code = _as_bool("show_code", True)
    cover.show_org = _as_bool("show_org", True)
    cover.show_manager = _as_bool("show_manager", True)
    cover.show_period = _as_bool("show_period", True)
    cover.cover_image_data_url = str(request.POST.get("cover_image_data_url", cover.cover_image_data_url or "")).strip()
    cover.save()
    _invalidate_project_cover_pdf_cache(project_id)
    return JsonResponse({"message": "표지 설정이 저장되었습니다."}, status=200)


@require_http_methods(["GET", "POST"])
def project_add_researcher_api(request, project_id: str):
    profile = effective_user_profile(request) or {}

    if request.method == "GET":
        if not project_repository.can_view_project(project_id, profile):
            return JsonResponse({"detail": "권한이 없습니다."}, status=403)
        groups = project_repository.project_researcher_groups(project_id)
        rows: list[dict] = []
        for group in groups:
            role = group.get("role")
            for member in group.get("members", []):
                rows.append({
                    "id": member.get("id"),
                    "name": member.get("name", "-"),
                    "username": member.get("username", "-"),
                    "email": member.get("email", "-"),
                    "organization": member.get("organization", "-"),
                    "status": member.get("status", "-"),
                    "role": role,
                })
        return JsonResponse(rows, safe=False)

    if not project_repository.can_manage_project_members(project_id, profile):
        return JsonResponse({"detail": "권한이 없습니다."}, status=403)

    user_id = request.POST.get("user_id", "")
    if not str(user_id).isdigit():
        return JsonResponse({"detail": "유효한 연구원을 선택하세요."}, status=400)

    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return JsonResponse({"detail": "프로젝트를 찾을 수 없습니다."}, status=404)

    user = UserAccount.objects.select_related("team").filter(id=int(user_id), is_approved=True).first()
    if not user:
        return JsonResponse({"detail": "연구원을 찾을 수 없습니다."}, status=404)

    if project.company_id and user.team_id != project.company_id:
        return JsonResponse({"detail": "우리팀 연구원만 추가할 수 있습니다."}, status=400)

    member_role = "admin" if user.role in {UserAccount.Role.OWNER, UserAccount.Role.ADMIN} else "member"
    _, created = ProjectMember.objects.get_or_create(
        project=project,
        user=user,
        defaults={"role": member_role, "contribution": "프로젝트 참여"},
    )
    if not created:
        return JsonResponse({"message": "이미 등록된 연구원입니다."}, status=200)
    return JsonResponse({"message": "연구자가 추가되었습니다."}, status=200)

@require_http_methods(["POST"])
def project_remove_researcher_api(request, project_id: str):
    profile = effective_user_profile(request) or {}
    if not project_repository.can_manage_project_members(project_id, profile):
        return JsonResponse({"detail": "권한이 없습니다."}, status=403)

@require_http_methods(["POST"])
def project_remove_researcher_api(request, project_id: str):
    profile = effective_user_profile(request) or {}
    if not project_repository.can_manage_project_members(project_id, profile):
        return JsonResponse({"detail": "권한이 없습니다."}, status=403)

    user_id = request.POST.get("user_id", "")
    if not str(user_id).isdigit():
        return JsonResponse({"detail": "유효한 연구원을 선택하세요."}, status=400)

    membership = ProjectMember.objects.select_related("user").filter(project_id=project_id, user_id=int(user_id)).first()
    if not membership or not membership.user:
        return JsonResponse({"detail": "프로젝트 연구자를 찾을 수 없습니다."}, status=404)

    if membership.user.role == UserAccount.Role.OWNER:
        return JsonResponse({"detail": "소유자는 프로젝트 연구자에서 제외할 수 없습니다."}, status=400)

    membership.delete()
    return JsonResponse({"message": "연구자가 제외되었습니다."}, status=200)


@require_GET
def dashboard_summary(_request):
    return JsonResponse(dashboard_counts())


@require_GET
@ensure_csrf_cookie
@login_required_page
def workflow_home_page(request):
    return redirect("/")
