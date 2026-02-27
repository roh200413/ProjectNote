from dataclasses import dataclass


@dataclass(frozen=True)
class CreateProjectCommand:
    name: str
    manager: str
    organization: str
    company_id: int | None
    code: str
    description: str
    start_date: str
    end_date: str
    status: str


@dataclass(frozen=True)
class InvitedMemberCommand:
    user_id: int
    role: str
