from collections import defaultdict
from datetime import datetime

from server.domains.research_notes.models import ResearchNote
from server.domains.admin.models import Team, UserAccount

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
        ids = [item.user_id for item in invited]
        users = {user.id: user for user in UserAccount.objects.select_related("team").filter(id__in=ids)}
        for item in invited:
            user = users.get(item.user_id)
            if not user:
                continue
            ProjectMember.objects.get_or_create(
                project=project,
                user=user,
                defaults={"role": item.role, "contribution": "프로젝트 참여"},
            )

    def ensure_creator_member(self, project: Project, user_profile: dict | None) -> None:
        if not user_profile:
            return

        user = None
        user_id = user_profile.get("id")
        if user_id:
            user = UserAccount.objects.select_related("team").filter(id=user_id).first()
        if not user:
            username = user_profile.get("username", "").strip()
            if username:
                user = UserAccount.objects.select_related("team").filter(username=username).first()
        if not user:
            return

        ProjectMember.objects.get_or_create(
            project=project,
            user=user,
            defaults={"role": "admin", "contribution": "프로젝트 생성자"},
        )

    def project_note_ids(self, project_id: str) -> list[str]:
        return [str(i) for i in ResearchNote.objects.filter(project_id=project_id).values_list("id", flat=True)]

    def project_researcher_groups(self, project_id: str) -> list[dict]:
        memberships = ProjectMember.objects.filter(project_id=project_id).select_related("user", "user__team")
        grouped = defaultdict(list)
        for member in memberships:
            if not member.user:
                continue
            org = member.user.team.name if member.user.team else "미지정"
            grouped[org].append(
                {
                    "name": member.user.display_name,
                    "role": member.role,
                    "organization": org,
                    "major": "미지정",
                    "contribution": member.contribution,
                }
            )

        groups = []
        for organization, members in grouped.items():
            groups.append(
                {
                    "group": f"{organization} 연구그룹",
                    "lead": members[0]["name"],
                    "members": members,
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
