import hashlib
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api import schemas
from app.core.config import settings
from app.db.base import get_db
from app.db.models import NoteEntry, NoteRevision, Organization, Project, User

router = APIRouter()


def _sha256_hex(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _build_chain_hash(previous_chain_hash: str | None, content_hash: str) -> str:
    payload = f"{previous_chain_hash or ''}:{content_hash}"
    return _sha256_hex(payload)


@router.get("/health", response_model=schemas.HealthResponse)
def health() -> schemas.HealthResponse:
    return schemas.HealthResponse()


@router.get("/frontend/bootstrap", response_model=schemas.FrontendBootstrapResponse)
def frontend_bootstrap() -> schemas.FrontendBootstrapResponse:
    return schemas.FrontendBootstrapResponse(
        api_name=settings.app_name,
        api_version="v1",
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/dashboard/summary", response_model=schemas.DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db)) -> schemas.DashboardSummary:
    organizations = db.query(func.count(Organization.id)).scalar() or 0
    projects = db.query(func.count(Project.id)).scalar() or 0
    notes = db.query(func.count(NoteEntry.id)).scalar() or 0
    revisions = db.query(func.count(NoteRevision.id)).scalar() or 0
    return schemas.DashboardSummary(
        organizations=organizations,
        projects=projects,
        notes=notes,
        revisions=revisions,
    )


@router.post("/users", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def create_user(payload: schemas.UserCreate, db: Session = Depends(get_db)) -> User:
    user = User(email=payload.email, full_name=payload.full_name)
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already exists") from exc
    db.refresh(user)
    return user


@router.post("/organizations", response_model=schemas.OrganizationOut, status_code=status.HTTP_201_CREATED)
def create_organization(payload: schemas.OrganizationCreate, db: Session = Depends(get_db)) -> Organization:
    org = Organization(name=payload.name, code=payload.code, created_by=payload.created_by)
    db.add(org)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Organization code already exists") from exc
    db.refresh(org)
    return org


@router.get("/organizations", response_model=list[schemas.OrganizationOut])
def list_organizations(db: Session = Depends(get_db)) -> list[Organization]:
    return db.query(Organization).filter(Organization.deleted_at.is_(None)).all()


@router.post("/projects", response_model=schemas.ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(payload: schemas.ProjectCreate, db: Session = Depends(get_db)) -> Project:
    org = db.get(Organization, payload.org_id)
    if not org or org.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Organization not found")

    project = Project(
        org_id=payload.org_id,
        name=payload.name,
        code=payload.code,
        pi_name=payload.pi_name,
        description=payload.description,
        start_date=payload.start_date,
        end_date=payload.end_date,
        duration_months=payload.duration_months,
        created_by=payload.created_by,
    )
    db.add(project)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Project code already exists in organization") from exc
    db.refresh(project)
    return project


@router.get("/projects", response_model=list[schemas.ProjectOut])
def list_projects(
    org_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[Project]:
    query = db.query(Project).filter(Project.deleted_at.is_(None))
    if org_id:
        query = query.filter(Project.org_id == org_id)
    return query.order_by(Project.created_at.desc()).all()


@router.post("/notes", response_model=schemas.NoteOut, status_code=status.HTTP_201_CREATED)
def create_note(payload: schemas.NoteCreate, db: Session = Depends(get_db)) -> NoteEntry:
    project = db.get(Project, payload.project_id)
    if not project or project.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        note = NoteEntry(
            project_id=payload.project_id,
            title=payload.title,
            entry_date=payload.entry_date,
            created_by=payload.created_by,
        )
        db.add(note)
        db.flush()

        content_hash = _sha256_hex(payload.content_md)
        chain_hash = _build_chain_hash(None, content_hash)
        revision = NoteRevision(
            note_id=note.id,
            rev_no=1,
            content_md=payload.content_md,
            content_json=payload.content_json,
            prev_hash=None,
            content_hash=content_hash,
            chain_hash=chain_hash,
            created_by=payload.created_by,
        )
        db.add(revision)
        db.flush()

        note.current_revision_id = revision.id
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(note)
    return note


@router.post(
    "/notes/{note_id}/revisions",
    response_model=schemas.NoteRevisionOut,
    status_code=status.HTTP_201_CREATED,
)
def create_note_revision(
    note_id: uuid.UUID,
    payload: schemas.NoteRevisionCreate,
    db: Session = Depends(get_db),
) -> NoteRevision:
    note = db.get(NoteEntry, note_id)
    if not note or note.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Note not found")

    last_revision = (
        db.query(NoteRevision)
        .filter(NoteRevision.note_id == note.id)
        .order_by(NoteRevision.rev_no.desc())
        .first()
    )
    if not last_revision:
        raise HTTPException(status_code=400, detail="Note has no baseline revision")

    try:
        content_hash = _sha256_hex(payload.content_md)
        chain_hash = _build_chain_hash(last_revision.chain_hash, content_hash)

        revision = NoteRevision(
            note_id=note.id,
            rev_no=last_revision.rev_no + 1,
            content_md=payload.content_md,
            content_json=payload.content_json,
            prev_hash=last_revision.chain_hash,
            content_hash=content_hash,
            chain_hash=chain_hash,
            created_by=payload.created_by,
        )
        db.add(revision)
        db.flush()

        note.current_revision_id = revision.id
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Revision conflict, retry") from exc

    db.refresh(revision)
    return revision


@router.get("/notes/{note_id}", response_model=schemas.NoteOut)
def get_note(note_id: uuid.UUID, db: Session = Depends(get_db)) -> NoteEntry:
    note = db.get(NoteEntry, note_id)
    if not note or note.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.get("/notes/{note_id}/revisions", response_model=list[schemas.NoteRevisionOut])
def list_note_revisions(note_id: uuid.UUID, db: Session = Depends(get_db)) -> list[NoteRevision]:
    note = db.get(NoteEntry, note_id)
    if not note or note.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Note not found")

    return (
        db.query(NoteRevision)
        .filter(NoteRevision.note_id == note_id)
        .order_by(NoteRevision.rev_no.asc())
        .all()
    )
