from collections import defaultdict
from datetime import datetime

from projectnote.workflow_app.models import Project, ProjectMember, ResearchNote, Researcher

from .entities import CreateProjectCommand, InvitedMemberCommand


class ProjectRepository:
    def list_projects(self) -> list[dict]:
        return [self.project_to_dict(project) for project in Project.objects.order_by("-created_at")]

    def get_project(self, project_id: str) -> Project:
        return Project.objects.get(id=project_id)

    def create_project(self, command: CreateProjectCommand) -> Project:
        start_date = datetime.strptime(command.start_date, "%Y-%m-%d").date() if command.start_date else None
        end_date = datetime.strptime(command.end_date, "%Y-%m-%d").date() if command.end_date else None
        return Project.objects.create(
            name=command.name,
            manager=command.manager,
            organization=command.organization,
            code=command.code,
            description=command.description,
            start_date=start_date,
            end_date=end_date,
            status=command.status or Project.Status.DRAFT,
        )

    def create_project_members(self, project: Project, invited: list[InvitedMemberCommand]) -> None:
        ids = [item.researcher_id for item in invited]
        researchers = {researcher.id: researcher for researcher in Researcher.objects.filter(id__in=ids)}
        for item in invited:
            researcher = researchers.get(item.researcher_id)
            if not researcher:
                continue
            ProjectMember.objects.get_or_create(
                project=project,
                researcher=researcher,
                defaults={"role": item.role, "contribution": "프로젝트 참여"},
            )

    def project_note_ids(self, project_id: str) -> list[str]:
        return [str(i) for i in ResearchNote.objects.filter(project_id=project_id).values_list("id", flat=True)]

    def project_researcher_groups(self, project_id: str) -> list[dict]:
        memberships = ProjectMember.objects.filter(project_id=project_id).select_related("researcher")
        grouped = defaultdict(list)
        for member in memberships:
            grouped[member.researcher.organization].append(member)

        groups = []
        for organization, members in grouped.items():
            groups.append(
                {
                    "group": f"{organization} 연구그룹",
                    "lead": members[0].researcher.name,
                    "members": [
                        {
                            "name": m.researcher.name,
                            "role": m.role,
                            "organization": m.researcher.organization,
                            "major": m.researcher.major,
                            "contribution": m.contribution,
                        }
                        for m in members
                    ],
                }
            )
        return groups

    @staticmethod
    def project_to_dict(project: Project) -> dict:
        return {
            "id": str(project.id),
            "name": project.name,
            "status": project.status,
            "manager": project.manager,
            "organization": project.organization,
            "code": project.code,
            "description": project.description,
            "start_date": project.start_date.isoformat() if project.start_date else "",
            "end_date": project.end_date.isoformat() if project.end_date else "",
        }
