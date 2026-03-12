from __future__ import annotations

from pathlib import Path

from django.conf import settings

from server.domains.projects.models import Project
from .models import ResearchNote

UNKNOWN_ORG_ID = "unknown-org"
PERSONAL_PROJECT_ID = "_personal"


def storage_root() -> Path:
    root = Path(settings.RESEARCH_NOTES_STORAGE_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _safe_segment(value: str | None, default: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return default
    return raw.replace("/", "_")


def org_id_for_project(project: Project | None) -> str:
    if not project:
        return UNKNOWN_ORG_ID
    return _safe_segment(str(project.company_id) if project.company_id else "", UNKNOWN_ORG_ID)


def project_id_for_note(note: ResearchNote | None) -> str:
    if not note or not note.project_id:
        return PERSONAL_PROJECT_ID
    return _safe_segment(str(note.project_id), PERSONAL_PROJECT_ID)


def org_id_for_note(note: ResearchNote | None) -> str:
    if not note:
        return UNKNOWN_ORG_ID
    project = getattr(note, "project", None)
    return org_id_for_project(project)


def project_root_for_project(project: Project | None) -> Path:
    project_id = _safe_segment(str(project.id) if project and project.id else "", PERSONAL_PROJECT_ID)
    return storage_root() / org_id_for_project(project) / project_id


def project_root_for_note(note: ResearchNote | None) -> Path:
    return storage_root() / org_id_for_note(note) / project_id_for_note(note)


def cover_root(project: Project | None) -> Path:
    return project_root_for_project(project) / "covers"


def notebooks_root(note: ResearchNote | None) -> Path:
    return project_root_for_note(note) / "notebooks"


def notebook_root(note: ResearchNote) -> Path:
    notebook_id = _safe_segment(str(note.id), "unknown-notebook")
    return notebooks_root(note) / notebook_id


def source_pdf_dir(note: ResearchNote) -> Path:
    return notebook_root(note) / "source" / "pdf"


def source_images_dir(note: ResearchNote) -> Path:
    return notebook_root(note) / "source" / "images"


def derived_pages_dir(note: ResearchNote) -> Path:
    return notebook_root(note) / "derived" / "pages"


def derived_assets_dir(note: ResearchNote) -> Path:
    return notebook_root(note) / "derived" / "assets"


def result_dir(note: ResearchNote) -> Path:
    return notebook_root(note) / "result"


def project_result_dir(project: Project | None) -> Path:
    return project_root_for_project(project) / "result"


def folder_relpath(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(storage_root().resolve()))
    except Exception:
        return str(path)
