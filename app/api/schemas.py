import uuid
from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field


class HealthResponse(BaseModel):
    status: str = "ok"


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    code: str | None = Field(default=None, max_length=30)
    created_by: uuid.UUID | None = None


class OrganizationOut(BaseModel):
    id: uuid.UUID
    name: str
    code: str | None
    status: str
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=200)


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    status: str

    class Config:
        from_attributes = True


class ProjectCreate(BaseModel):
    org_id: uuid.UUID
    name: str = Field(min_length=1, max_length=100)
    code: str | None = Field(default=None, max_length=25)
    pi_name: str | None = Field(default=None, max_length=20)
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    duration_months: int | None = Field(default=None, ge=1)
    created_by: uuid.UUID | None = None


class ProjectOut(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    name: str
    code: str | None
    status: str

    class Config:
        from_attributes = True


class NoteCreate(BaseModel):
    project_id: uuid.UUID
    title: str = Field(min_length=1, max_length=255)
    entry_date: date
    content_md: str = Field(min_length=1)
    content_json: dict
    created_by: uuid.UUID | None = None


class NoteRevisionCreate(BaseModel):
    content_md: str = Field(min_length=1)
    content_json: dict
    created_by: uuid.UUID | None = None


class NoteOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    entry_date: date
    current_revision_id: uuid.UUID | None

    class Config:
        from_attributes = True


class NoteRevisionOut(BaseModel):
    id: uuid.UUID
    note_id: uuid.UUID
    rev_no: int
    content_hash: str
    chain_hash: str
    created_at: datetime

    class Config:
        from_attributes = True
