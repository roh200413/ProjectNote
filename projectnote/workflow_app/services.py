import json

from .domain import CreateProjectCommand, InvitedMemberCommand
from .repositories import WorkflowRepository


class WorkflowService:
    def __init__(self, repository: WorkflowRepository | None = None) -> None:
        self.repository = repository or WorkflowRepository()

    def create_project(self, post_data) -> dict:
        command = CreateProjectCommand(
            name=post_data.get("name", "새 프로젝트"),
            manager=post_data.get("manager", "미지정"),
            organization=post_data.get("organization", "미지정"),
            code=post_data.get("code", ""),
            description=post_data.get("description", ""),
            start_date=post_data.get("start_date", ""),
            end_date=post_data.get("end_date", ""),
            status=post_data.get("status", "draft"),
        )
        project = self.repository.create_project(command)

        invited_payload = post_data.get("invited_members", "[]")
        invited = []
        try:
            invited_members = json.loads(invited_payload)
            if isinstance(invited_members, list):
                for invited_member in invited_members:
                    researcher_id = invited_member.get("id")
                    if not researcher_id:
                        continue
                    invited.append(InvitedMemberCommand(researcher_id=int(researcher_id), role=invited_member.get("role", "member")))
        except (json.JSONDecodeError, TypeError, ValueError):
            invited = []

        self.repository.create_project_members(project, invited)
        return self.repository._project_to_dict(project)
