from pydantic import BaseModel, Field


class InvitedMemberPayload(BaseModel):
    id: int = Field(gt=0)
    role: str = "member"


class CreateProjectPayload(BaseModel):
    name: str = "새 프로젝트"
    manager: str = "미지정"
    organization: str = "미지정"
    code: str = ""
    description: str = ""
    start_date: str = ""
    end_date: str = ""
    status: str = "draft"
    invited_members: list[InvitedMemberPayload] = Field(default_factory=list)
