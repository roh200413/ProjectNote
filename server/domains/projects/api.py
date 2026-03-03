import base64
import json
import uuid
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.db import OperationalError, ProgrammingError
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import render
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
from server.application.web_support import (
    json_uuid_validation_error,
    login_required_page,
    page_context,
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


@require_GET
def projects(request):
    org_id = request.GET.get("org_id")
    if org_id:
        try:
            uuid.UUID(org_id)
        except ValueError:
            return json_uuid_validation_error("org_id", org_id)
    return JsonResponse(project_repository.list_projects(), safe=False)


@require_http_methods(["GET", "POST"])
def project_management_api(request):
    if request.method == "GET":
        return JsonResponse(project_repository.list_projects(), safe=False)
    payload = request.POST.copy()
    team_id = request.session.get("user_profile", {}).get("team_id")
    if team_id:
        payload["company_id"] = str(team_id)
    project = project_service.create_project(payload, request.session.get("user_profile", {}))
    return JsonResponse(project, status=201)


@require_GET
@ensure_csrf_cookie
@login_required_page
def project_management_page(request):
    profile = effective_user_profile(request) or {}
    return render(request, "workflow/projects.html", page_context(request, {"projects": project_repository.visible_projects_for_user(profile)}))


@require_GET
@ensure_csrf_cookie
@login_required_page
def project_create_page(request):
    profile = effective_user_profile(request) or {}
    team_id = profile.get("team_id")
    manager_options = _manager_options_for_team(team_id)
    default_manager = profile.get("username", "")
    return render(
        request,
        "workflow/project_create.html",
        page_context(
            request,
            {
                "user_groups": admin_repository.user_groups_for_selection(team_id),
                "manager_options": manager_options,
                "default_manager": default_manager,
            },
        ),
    )


@require_GET
@ensure_csrf_cookie
@login_required_page
def project_detail_page(request, project_id: str):
    profile = effective_user_profile(request) or {}
    if not project_repository.can_view_project(project_id, profile):
        raise Http404("Project not found")
    try:
        project_obj = Project.objects.get(id=project_id)
        project = project_repository.project_to_dict(project_obj)
    except Project.DoesNotExist as exc:
        raise Http404("Project not found") from exc

    note_ids = project_repository.project_note_ids(project_id)
    all_notes = research_note_repository.list_research_notes()
    project_notes = [note for note in all_notes if note["id"] in note_ids]
    selected_note = project_notes[0] if project_notes else None
    selected_note_files = research_note_repository.list_note_files(selected_note["id"]) if selected_note else []
    manager_options = _manager_options_for_team(profile.get("team_id"))
    manager_display = next((item["display_name"] for item in manager_options if item["username"] == project.get("manager")), project.get("manager", "-"))
    cover_data = _load_cover_data(project_obj, project, manager_display)
    return render(
        request,
        "workflow/project_detail.html",
        page_context(
            request,
            {
                "project": project,
                "project_notes": project_notes,
                "researcher_groups": project_repository.project_researcher_groups(project_id),
                "selected_note": selected_note,
                "selected_note_files": selected_note_files,
                "manager_options": manager_options,
                "manager_display": manager_display,
                "cover_data": cover_data,
            },
        ),
    )




@require_GET
@ensure_csrf_cookie
@login_required_page
def project_researchers_page(request, project_id: str):
    profile = effective_user_profile(request) or {}
    if not project_repository.can_view_project(project_id, profile):
        raise Http404("Project not found")
    try:
        project = project_repository.project_to_dict(Project.objects.get(id=project_id))
    except Project.DoesNotExist as exc:
        raise Http404("Project not found") from exc

    researcher_groups = project_repository.project_researcher_groups(project_id)
    existing_member_ids = {
        member["id"]
        for group in researcher_groups
        for member in group.get("members", [])
    }
    raw_team_groups = admin_repository.user_groups_for_selection((effective_user_profile(request) or {}).get("team_id"))
    filtered_team_groups = []
    for group in raw_team_groups:
        filtered_members = [
            member
            for member in group.get("members", [])
            if member.get("id") not in existing_member_ids and not bool(member.get("is_owner", False))
        ]
        if filtered_members:
            filtered_team_groups.append({**group, "members": filtered_members, "lead": filtered_members[0]["name"]})

    return render(
        request,
        "workflow/project_researchers.html",
        page_context(
            request,
            {
                "project": project,
                "researcher_groups": researcher_groups,
                "team_user_groups": filtered_team_groups,
                "can_manage_project_members": project_repository.can_manage_project_members(project_id, profile),
            },
        ),
    )



@require_GET
@ensure_csrf_cookie
@login_required_page
def project_research_notes_page(request, project_id: str):
    profile = effective_user_profile(request) or {}
    if not project_repository.can_view_project(project_id, profile):
        raise Http404("Project not found")
    try:
        project = project_repository.project_to_dict(Project.objects.get(id=project_id))
    except Project.DoesNotExist as exc:
        raise Http404("Project not found") from exc

    note_ids = project_repository.project_note_ids(project_id)
    all_notes = research_note_repository.list_research_notes()
    project_notes = [note for note in all_notes if note["id"] in note_ids]

    file_rows = []
    for note in project_notes:
        for file in research_note_repository.list_note_files(note["id"]):
            file_rows.append({
                "note_title": note["title"],
                "name": file["name"],
                "format": file["format"],
                "created": file["created"],
                "author": file["author"],
                "note_id": note["id"],
                "file_id": file["id"],
            })

    author_options = []
    seen_authors = set()
    current_author = str(profile.get("name") or profile.get("username") or "").strip()
    if current_author:
        author_options.append(current_author)
        seen_authors.add(current_author)
    for group in project_repository.project_researcher_groups(project_id):
        for member in group.get("members", []):
            name = str(member.get("name") or "").strip()
            if name and name not in seen_authors:
                author_options.append(name)
                seen_authors.add(name)

    return render(
        request,
        "workflow/project_research_notes.html",
        page_context(
            request,
            {
                "project": project,
                "project_notes": project_notes,
                "project_files": file_rows,
                "note_count": len(project_notes),
                "file_count": len(file_rows),
                "author_options": author_options,
                "default_author": current_author,
            },
        ),
    )



@require_GET
@ensure_csrf_cookie
@login_required_page
def project_research_notes_print_page(request, project_id: str):
    profile = effective_user_profile(request) or {}
    if not project_repository.can_view_project(project_id, profile):
        raise Http404("Project not found")

    try:
        project_obj = Project.objects.get(id=project_id)
        project = project_repository.project_to_dict(project_obj)
    except Project.DoesNotExist as exc:
        raise Http404("Project not found") from exc

    note_ids = project_repository.project_note_ids(project_id)
    all_notes = research_note_repository.list_research_notes()
    project_notes = [note for note in all_notes if note["id"] in note_ids]

    manager_display = project.get("manager", "-")
    manager_user = UserAccount.objects.filter(username=manager_display).first() or UserAccount.objects.filter(display_name=manager_display).first()
    manager_signature = signature_repository.read_signature(manager_user.username) if manager_user else {"signature_data_url": ""}

    cover_data = _load_cover_data(project_obj, project, manager_display)

    def _period_text() -> str:
        if not cover_data.get("show_period"):
            return ""
        start = str(cover_data.get("start_date") or "").strip()
        end = str(cover_data.get("end_date") or "").strip()
        if start and end:
            return f"{start} ~ {end}"
        return start or end

    printable_files = []
    for note in project_notes:
        for file in research_note_repository.list_note_files(note["id"]):
            author_name = str(file.get("author") or "-")
            author_user = UserAccount.objects.filter(username=author_name).first() or UserAccount.objects.filter(display_name=author_name).first()
            author_signature = signature_repository.read_signature(author_user.username) if author_user else {"signature_data_url": ""}
            printable_files.append(
                {
                    "note_title": note["title"],
                    "name": file["name"],
                    "format": file["format"],
                    "created": file.get("created", "-"),
                    "author": author_name,
                    "manager_name": manager_user.display_name if manager_user else manager_display,
                    "reviewer_date": datetime.now().strftime("%Y.%m.%d / %I:%M %p"),
                    "author_signature_data_url": author_signature.get("signature_data_url", ""),
                    "manager_signature_data_url": manager_signature.get("signature_data_url", ""),
                    "content_url": f"/frontend/research-notes/{note['id']}/files/{file['id']}/content",
                }
            )

    return render(
        request,
        "workflow/project_research_notes_print.html",
        page_context(
            request,
            {
                "project": project,
                "cover_data": cover_data,
                "period_text": _period_text(),
                "printable_files": printable_files,
            },
        ),
    )


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

            page_buffer = BytesIO()
            pdf = canvas.Canvas(page_buffer, pagesize=A4)
            pw, ph = A4
            # 화면 그대로 A4로 맞춰 삽입
            pdf.drawImage(reader, 0, 0, width=pw, height=ph, preserveAspectRatio=False)
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

    # 1) 표지 PDF(A4)를 먼저 생성
    cover_buffer = BytesIO()
    c = canvas.Canvas(cover_buffer, pagesize=A4)
    w, h = A4

    cover_image_data_url = str(cover_data.get("cover_image_data_url") or "")
    cover_mime, cover_payload = _decode_data_url(cover_image_data_url)

    cover_pdf_reader = None
    if cover_mime == "application/pdf" and cover_payload:
        try:
            cover_pdf_reader = PdfReader(BytesIO(cover_payload), strict=False)
        except Exception:
            cover_pdf_reader = None

    drew_cover_image = False
    if cover_mime.startswith("image/") and cover_payload:
        try:
            img_reader = ImageReader(BytesIO(cover_payload))
            c.drawImage(img_reader, 0, 0, width=w, height=h, preserveAspectRatio=False)
            drew_cover_image = True
        except Exception:
            drew_cover_image = False

    if not drew_cover_image:
        _set_pdf_font(c, 16, bold=True)
        c.drawCentredString(w / 2, h - 80, "Electronic Lab Notebook")
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

    def _find_source_file(note_id: str, file_name: str):
        safe_name = Path(file_name).name
        candidates = [Path(folder) / safe_name for folder in research_note_repository.list_note_folders(note_id)]
        if not candidates:
            storage_root = Path(settings.RESEARCH_NOTES_STORAGE_ROOT)
            candidates = list(storage_root.glob(f"*/{note_id}/{safe_name}"))
        return next((candidate for candidate in candidates if candidate.exists() and candidate.is_file()), None)

    def _image_reader_from_data_url(data_url: str):
        raw = str(data_url or "")
        if not raw.startswith("data:image") or "," not in raw:
            return None
        try:
            encoded = raw.split(",", 1)[1]
            return ImageReader(BytesIO(base64.b64decode(encoded)))
        except Exception:
            return None

    def _draw_signature_panel(pdf, pw, ph, *, author_name: str, created_text: str, reviewer_name: str, reviewer_date: str, author_signature_data_url: str, manager_signature_data_url: str):
        top = 40
        left = 24
        total_width = pw - 48
        col = total_width / 4
        box_h = 64
        labels = ["작성자 / 작성일", "작성자 사인", "점검자 / 점검일자", "점검자 사인"]
        values = [f"{author_name}\n{created_text}", "", f"{reviewer_name}\n{reviewer_date}", ""]
        for idx in range(4):
            x = left + idx * col
            pdf.rect(x, top, col, box_h)
            _set_pdf_font(pdf, 9)
            pdf.drawString(x + 4, top + box_h - 12, labels[idx])
            if idx in {0, 2}:
                _set_pdf_font(pdf, 10)
                for n, line in enumerate(values[idx].split("\n")):
                    pdf.drawCentredString(x + col / 2, top + 28 - (n * 12), line)
            else:
                data_url = author_signature_data_url if idx == 1 else manager_signature_data_url
                reader = _image_reader_from_data_url(data_url)
                if reader:
                    pdf.drawImage(reader, x + 8, top + 6, width=col - 16, height=32, preserveAspectRatio=True, anchor='c')
                else:
                    _set_pdf_font(pdf, 9)
                    pdf.drawCentredString(x + col / 2, top + 20, "사인 없음")

    def _overlay_signature_on_pdf_page(page, *, author_name: str, created_text: str, reviewer_name: str, reviewer_date: str, author_signature_data_url: str, manager_signature_data_url: str):
        pw = float(page.mediabox.width)
        ph = float(page.mediabox.height)
        page_buffer = BytesIO()
        pdf = canvas.Canvas(page_buffer, pagesize=(pw, ph))
        _draw_signature_panel(
            pdf,
            pw,
            ph,
            author_name=author_name,
            created_text=created_text,
            reviewer_name=reviewer_name,
            reviewer_date=reviewer_date,
            author_signature_data_url=author_signature_data_url,
            manager_signature_data_url=manager_signature_data_url,
        )
        pdf.save()
        page_buffer.seek(0)
        overlay_reader = PdfReader(page_buffer, strict=False)
        page.merge_page(overlay_reader.pages[0])

    def _build_single_page_pdf(title: str, subtitle: str, content_builder):
        page_buffer = BytesIO()
        pdf = canvas.Canvas(page_buffer, pagesize=A4)
        pw, ph = A4
        _set_pdf_font(pdf, 14, bold=True)
        pdf.drawString(40, ph - 50, title)
        _set_pdf_font(pdf, 11)
        pdf.drawString(40, ph - 68, subtitle)
        content_builder(pdf, pw, ph)
        pdf.showPage()
        pdf.save()
        page_buffer.seek(0)
        return PdfReader(page_buffer, strict=False)

    # 2) PDF 단순 병합 (표지 + 각 연구파일을 순서대로)
    writer = PdfWriter()
    if cover_pdf_reader:
        writer.append(cover_pdf_reader)
    else:
        writer.append(PdfReader(cover_buffer, strict=False))

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
    image_exts = {"png", "jpg", "jpeg", "webp"}

    for note in project_notes:
        for file in research_note_repository.list_note_files(note["id"]):
            file_id = str(file.get("id") or "").strip()
            note_id = str(note["id"])
            if selected_pairs and (note_id, file_id) not in selected_pairs:
                continue
            total_files += 1
            fmt = str(file.get("format", "")).lower()
            file_title = f"[{note['title']}] {file.get('name', '-') }"
            source = _find_source_file(note["id"], str(file.get("name", "")))

            author_name = str(file.get("author") or "-")
            created_text = str(file.get("created") or "-")
            reviewer_date = datetime.now().strftime("%Y.%m.%d / %I:%M %p")
            author_user = UserAccount.objects.filter(username=author_name).first() or UserAccount.objects.filter(display_name=author_name).first()
            author_signature_data_url = signature_repository.read_signature(author_user.username).get("signature_data_url", "") if author_user else ""
            manager_user = UserAccount.objects.filter(username=manager_display).first() or UserAccount.objects.filter(display_name=manager_display).first()
            manager_signature_data_url = signature_repository.read_signature(manager_user.username).get("signature_data_url", "") if manager_user else ""

            if fmt == "pdf" and source:
                try:
                    with source.open("rb") as pdf_file:
                        reader = PdfReader(pdf_file, strict=False)
                        if getattr(reader, "is_encrypted", False):
                            try:
                                reader.decrypt("")
                            except Exception:
                                pass
                        page_count = len(reader.pages)
                        for idx, page in enumerate(reader.pages):
                            if idx == page_count - 1:
                                _overlay_signature_on_pdf_page(
                                    page,
                                    author_name=author_name,
                                    created_text=created_text,
                                    reviewer_name=manager_display,
                                    reviewer_date=reviewer_date,
                                    author_signature_data_url=author_signature_data_url,
                                    manager_signature_data_url=manager_signature_data_url,
                                )
                            writer.add_page(page)
                    merged_files += 1
                    continue
                except Exception:
                    pass

            if fmt in image_exts and source:
                try:
                    def _draw_image(pdf, pw, ph, source_path=str(source)):
                        left, bottom, width, height = 40, 130, pw - 80, ph - 250
                        pdf.drawImage(source_path, left, bottom, width=width, height=height, preserveAspectRatio=True, anchor='c')
                        _draw_signature_panel(
                            pdf,
                            pw,
                            ph,
                            author_name=author_name,
                            created_text=created_text,
                            reviewer_name=manager_display,
                            reviewer_date=reviewer_date,
                            author_signature_data_url=author_signature_data_url,
                            manager_signature_data_url=manager_signature_data_url,
                        )
                    writer.append(_build_single_page_pdf(file_title, f"형식: {fmt.upper()}", _draw_image))
                    merged_files += 1
                    continue
                except Exception:
                    pass

            def _draw_placeholder(pdf, pw, ph, fmt_text=fmt):
                _set_pdf_font(pdf, 12)
                pdf.drawString(40, ph - 110, f"해당 파일 형식({fmt_text or '알수없음'})은 PDF 병합 미지원 형식입니다.")
                pdf.drawString(40, ph - 130, "원본은 프로젝트 연구노트 화면에서 개별 확인해주세요.")
                _draw_signature_panel(
                    pdf,
                    pw,
                    ph,
                    author_name=author_name,
                    created_text=created_text,
                    reviewer_name=manager_display,
                    reviewer_date=reviewer_date,
                    author_signature_data_url=author_signature_data_url,
                    manager_signature_data_url=manager_signature_data_url,
                )

            writer.append(_build_single_page_pdf(file_title, f"형식: {fmt.upper() if fmt else '-'}", _draw_placeholder))
            merged_files += 1

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

    upload = request.FILES.get("research_note_file")
    if not upload:
        return JsonResponse({"message": "업로드할 파일이 없습니다."}, status=400)

    safe_name = Path(upload.name).name
    extension = Path(safe_name).suffix.lstrip(".").lower()
    allowed_extensions = {
        "jpeg", "jpg", "png", "svg", "tiff", "webp", "heif", "heic", "doc", "docx", "pptx", "ppt", "xls", "xlsx", "pdf"
    }
    if extension not in allowed_extensions:
        return JsonResponse({"message": "지원하지 않는 파일 형식입니다."}, status=400)

    owner_name = str(profile.get("name") or profile.get("username") or "미지정").strip() or "미지정"
    title = str(request.POST.get("title", "")).strip() or safe_name
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

    storage_root = Path(settings.RESEARCH_NOTES_STORAGE_ROOT)
    note = ResearchNote.objects.create(
        project=project,
        title=title,
        owner=owner_name,
        project_code=project.code,
        period=updated_text,
        files=1,
        members=1,
        summary=summary,
    )

    username = str(profile.get("username") or "anonymous").strip() or "anonymous"
    note_folder = storage_root / username / str(note.id)
    note_folder.mkdir(parents=True, exist_ok=True)
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
    ResearchNoteFolder.objects.create(note=note, name=str(note_folder))

    return JsonResponse({"message": "연구파일이 등록되었습니다.", "note_id": str(note.id)}, status=201)


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
    data_url = str(cover_data.get("cover_image_data_url") or "")
    mime, payload = _decode_data_url(data_url)

    if mime == "application/pdf" and payload:
        return FileResponse(BytesIO(payload), as_attachment=True, filename=f"project_{project_id}_cover.pdf", content_type="application/pdf")

    # image/unknown fallback: generate A4 PDF using saved image when present, else text cover
    cover_buffer = BytesIO()
    c = canvas.Canvas(cover_buffer, pagesize=A4)
    w, h = A4

    drew_image = False
    if mime.startswith("image/") and payload:
        try:
            reader = ImageReader(BytesIO(payload))
            c.drawImage(reader, 0, 0, width=w, height=h, preserveAspectRatio=False)
            drew_image = True
        except Exception:
            drew_image = False

    if not drew_image:
        _set_pdf_font(c, 16, bold=True)
        c.drawCentredString(w / 2, h - 80, "Electronic Lab Notebook")
        _set_pdf_font(c, 26, bold=True)
        c.drawCentredString(w / 2, h - 130, "연구노트")
        if cover_data.get("show_title"):
            _set_pdf_font(c, 22, bold=True)
            c.drawCentredString(w / 2, h - 170, str(cover_data.get("title") or ""))

    c.showPage()
    c.save()
    cover_buffer.seek(0)
    return FileResponse(cover_buffer, as_attachment=True, filename=f"project_{project_id}_cover.pdf", content_type="application/pdf")


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


@require_http_methods(["POST"])
def project_cover_update_api(request, project_id: str):
    profile = effective_user_profile(request) or {}
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
    return JsonResponse({"message": "표지 설정이 저장되었습니다."}, status=200)


@require_http_methods(["POST"])
def project_add_researcher_api(request, project_id: str):
    profile = effective_user_profile(request) or {}
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
    cards = [
        {"title": "프로젝트 생성", "href": "/frontend/projects/create", "description": "신규 프로젝트를 생성합니다."},
        {"title": "프로젝트 관리", "href": "/frontend/projects", "description": "생성된 프로젝트 목록/상세를 관리합니다."},
        {"title": "연구자 관리", "href": "/frontend/researchers", "description": "연구자 등록 및 소속/역할 정보를 관리합니다."},
        {"title": "데이터 업데이트", "href": "/frontend/data-updates", "description": "데이터 업데이트 이력을 기록합니다."},
    ]
    projects = project_repository.list_projects()
    current_name = request.session.get("user_profile", {}).get("name", "")
    managed_projects = [project for project in projects if project.get("manager") == current_name]
    return render(
        request,
        "workflow/home.html",
        page_context(request, {"cards": cards, "managed_projects": managed_projects}),
    )
