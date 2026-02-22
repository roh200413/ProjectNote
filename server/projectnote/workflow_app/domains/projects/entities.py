from dataclasses import dataclass


@dataclass(frozen=True)
class CreateProjectCommand:
    name: str
    manager: str
    organization: str
    code: str
    description: str
    start_date: str
    end_date: str
    status: str


@dataclass(frozen=True)
class InvitedMemberCommand:
    researcher_id: int
    role: str
