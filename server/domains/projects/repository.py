from collections import defaultdict
from datetime import datetime

from server.domains.research_notes.models import ResearchNote
from server.domains.admin.models import Team, UserAccount

from .models import Project, ProjectMember

from .entities import CreateProjectCommand, InvitedMemberCommand


class ProjectRepository:
    def list_projects(self) -> list[dict]:
        return [self.project_to_dict(project) for project in Project.objects.order_by("-created_at")]

    def visible_projects_for_user(self, profile: dict | None) -> list[dict]:
        if not profile:
            return []

        if profile.get("is_super_admin"):
            return self.list_projects()

        username = str(profile.get("username", "")).strip()
        if not username:
            return []

        user = UserAccount.objects.filter(username=username).first()
        if not user:
            return []

        if user.role in {UserAccount.Role.OWNER, UserAccount.Role.ADMIN}:
            if user.team_id:
                projects = Project.objects.filter(company_id=user.team_id).order_by("-created_at")
            else:
                projects = Project.objects.order_by("-created_at")
            return [self.project_to_dict(project) for project in projects]

        project_ids = ProjectMember.objects.filter(user_id=user.id).values_list("project_id", flat=True)
        projects = Project.objects.filter(id__in=project_ids).order_by("-created_at")
        return [self.project_to_dict(project) for project in projects]

    def can_view_project(self, project_id: str, profile: dict | None) -> bool:
        if not profile:
            return False
        if profile.get("is_super_admin"):
            return True
        username = str(profile.get("username", "")).strip()
        if not username:
            return False
        user = UserAccount.objects.filter(username=username).first()
        if not user:
            return False
        if user.role in {UserAccount.Role.OWNER, UserAccount.Role.ADMIN}:
            return True
        return ProjectMember.objects.filter(project_id=project_id, user_id=user.id).exists()

    def can_manage_project_members(self, project_id: str, profile: dict | None) -> bool:
        if not profile:
            return False
        if profile.get("is_super_admin"):
            return True
        username = str(profile.get("username", "")).strip()
        if not username:
            return False
        user = UserAccount.objects.select_related("team").filter(username=username).first()
        if not user or user.role not in {UserAccount.Role.OWNER, UserAccount.Role.ADMIN}:
            return False
        project = Project.objects.filter(id=project_id).first()
        if not project:
            return False
        if user.team_id and project.company_id:
            return user.team_id == project.company_id
        return True

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

    def update_project(self, project_id: str, payload: dict) -> dict:
        project = Project.objects.filter(id=project_id).first()
        if not project:
            raise ValueError("프로젝트를 찾을 수 없습니다.")

        for field in ["name", "manager", "organization", "code", "description", "status"]:
            if field in payload:
                setattr(project, field, payload[field])

        if "start_date" in payload:
            project.start_date = datetime.strptime(payload["start_date"], "%Y-%m-%d").date() if payload["start_date"] else None
        if "end_date" in payload:
            project.end_date = datetime.strptime(payload["end_date"], "%Y-%m-%d").date() if payload["end_date"] else None

        project.save()
        return self.project_to_dict(project)

    def add_project_member(self, project_id: str, user_id: int) -> None:
        project = Project.objects.filter(id=project_id).first()
        if not project:
            raise ValueError("프로젝트를 찾을 수 없습니다.")

        user = UserAccount.objects.select_related("team").filter(id=user_id, is_approved=True).first()
        if not user:
            raise ValueError("추가할 수 있는 연구원이 아닙니다.")

        if project.company_id and user.team_id != project.company_id:
            raise ValueError("우리팀 연구원만 추가할 수 있습니다.")

        ProjectMember.objects.get_or_create(
            project=project,
            user=user,
            defaults={"role": "member", "contribution": "프로젝트 참여"},
        )

    def remove_project_member(self, project_id: str, user_id: int) -> None:
        membership = ProjectMember.objects.select_related("user").filter(project_id=project_id, user_id=user_id).first()
        if not membership:
            raise ValueError("프로젝트에 참여 중인 연구원이 아닙니다.")
        if membership.user and membership.user.role == UserAccount.Role.OWNER:
            raise ValueError("소유자는 프로젝트 연구자에서 제외할 수 없습니다.")
        membership.delete()

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
            is_owner = member.user.role == UserAccount.Role.OWNER
            grouped[org].append(
                {
                    "id": member.user.id,
                    "name": member.user.display_name,
                    "role": "소유자" if is_owner else member.role,
                    "organization": org,
                    "major": "미지정",
                    "contribution": member.contribution,
                    "is_owner": is_owner,
                }
            )

        groups = []
        for organization, members in grouped.items():
            members.sort(key=lambda item: (0 if item.get("is_owner") else 1, item.get("name", "")))
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
