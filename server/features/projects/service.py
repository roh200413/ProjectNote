import json

from .entities import CreateProjectCommand, InvitedMemberCommand
from .repository import ProjectRepository
from .schemas import CreateProjectPayload


class ProjectService:
    def __init__(self, project_repository: ProjectRepository | None = None) -> None:
        self.project_repository = project_repository or ProjectRepository()

    def create_project(self, post_data) -> dict:
        invited_payload = post_data.get("invited_members", "[]")
        invited_members = []
        try:
            parsed = json.loads(invited_payload)
            if isinstance(parsed, list):
                invited_members = parsed
        except json.JSONDecodeError:
            invited_members = []

        payload = CreateProjectPayload(
            name=post_data.get("name", "새 프로젝트"),
            manager=post_data.get("manager", "미지정"),
            organization=post_data.get("organization", "미지정"),
            code=post_data.get("code", ""),
            description=post_data.get("description", ""),
            start_date=post_data.get("start_date", ""),
            end_date=post_data.get("end_date", ""),
            status=post_data.get("status", "draft"),
            invited_members=invited_members,
        )

        command = CreateProjectCommand(
            name=payload.name,
            manager=payload.manager,
            organization=payload.organization,
            code=payload.code,
            description=payload.description,
            start_date=payload.start_date,
            end_date=payload.end_date,
            status=payload.status,
        )
        project = self.project_repository.create_project(command)

        invited_commands = [
            InvitedMemberCommand(researcher_id=member.id, role=member.role)
            for member in payload.invited_members
        ]
        self.project_repository.create_project_members(project, invited_commands)
        return self.project_repository.project_to_dict(project)
