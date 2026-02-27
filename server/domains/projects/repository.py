from collections import defaultdict
from datetime import datetime

from server.domains.research_notes.models import ResearchNote
from server.domains.admin.models import Team
from server.domains.researchers.models import Researcher

from .models import Project, ProjectMember

from .entities import CreateProjectCommand, InvitedMemberCommand


class ProjectRepository:
    def list_projects(self) -> list[dict]:
        return [self.project_to_dict(project) for project in Project.objects.order_by("-created_at")]

    def get_project(self, project_id: str) -> Project:
        return Project.objects.get(id=project_id)

    def create_project(self, command: CreateProjectCommand) -> Project:
        start_date = datetime.strptime(command.start_date, "%Y-%m-%d").date() if command.start_date else None
        end_date = datetime.strptime(command.end_date, "%Y-%m-%d").date() if command.end_date else None
        company = Team.objects.filter(id=command.company_id).first() if command.company_id else None
        organization = company.name if company else command.organization
        return Project.objects.create(
            name=command.name,
            manager=command.manager,
            organization=organization,
            company=company,
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

    def ensure_creator_member(self, project: Project, user_profile: dict | None) -> None:
        if not user_profile:
            return

        email = user_profile.get("email", "").strip()
        if not email:
            return

        name = user_profile.get("name", "미지정").strip() or "미지정"
        organization = user_profile.get("organization", "미지정").strip() or "미지정"
        major = user_profile.get("major", "미지정").strip() or "미지정"

        researcher, _ = Researcher.objects.get_or_create(
            email=email,
            defaults={
                "name": name,
                "role": "관리자",
                "organization": organization,
                "major": major,
                "status": "활성",
            },
        )

        ProjectMember.objects.get_or_create(
            project=project,
            researcher=researcher,
            defaults={"role": "admin", "contribution": "프로젝트 생성자"},
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
            "company_id": project.company_id,
            "company_name": project.company.name if project.company else project.organization,
            "code": project.code,
            "description": project.description,
            "start_date": project.start_date.isoformat() if project.start_date else "",
            "end_date": project.end_date.isoformat() if project.end_date else "",
        }
