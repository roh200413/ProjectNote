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
            business_name=command.business_name,
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
        raw_user_id = user_profile.get("id")
        user_id = None
        if isinstance(raw_user_id, int):
            user_id = raw_user_id
        elif isinstance(raw_user_id, str) and raw_user_id.isdigit():
            user_id = int(raw_user_id)

        if user_id is not None:
            user = UserAccount.objects.select_related("team").filter(id=user_id).first()

        if not user:
            username = str(user_profile.get("username", "")).strip()
            if username:
                user = UserAccount.objects.select_related("team").filter(username=username).first()
        if not user:
            return

        ProjectMember.objects.get_or_create(
            project=project,
            user=user,
            defaults={"role": "admin", "contribution": "프로젝트 생성자"},
        )

    def update_project(self, project_id: str, payload: dict) -> dict:
        project = Project.objects.filter(id=project_id).first()
        if not project:
            raise ValueError("프로젝트를 찾을 수 없습니다.")

        project.name = str(payload.get("name") or project.name).strip() or project.name
        project.manager = str(payload.get("manager") or project.manager).strip()
        if hasattr(project, "business_name"):
            project.business_name = str(payload.get("business_name") or project.business_name).strip()
        project.organization = str(payload.get("organization") or project.organization).strip()
        project.code = str(payload.get("code") or project.code).strip()
        project.description = str(payload.get("description") or project.description).strip()

        start_raw = str(payload.get("start_date") or "").strip()
        end_raw = str(payload.get("end_date") or "").strip()
        if start_raw:
            try:
                project.start_date = datetime.strptime(start_raw, "%Y-%m-%d").date()
            except ValueError:
                pass
        else:
            project.start_date = None
        if end_raw:
            try:
                project.end_date = datetime.strptime(end_raw, "%Y-%m-%d").date()
            except ValueError:
                pass
        else:
            project.end_date = None

        status = str(payload.get("status") or "").strip()
        if status in {choice for choice, _ in Project.Status.choices}:
            project.status = status

        project.save()
        return self.project_to_dict(project)

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
                    "id": member.user.id,
                    "name": member.user.display_name,
                    "role": member.role,
                    "organization": org,
                    "major": "미지정",
                    "contribution": member.contribution,
                    "is_owner": member.user.role == UserAccount.Role.OWNER,
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
            "business_name": project.business_name,
            "organization": project.organization,
            "company_id": project.company_id,
            "company_name": project.company.name if project.company else project.organization,
            "code": project.code,
            "description": project.description,
            "start_date": project.start_date.isoformat() if project.start_date else "",
            "end_date": project.end_date.isoformat() if project.end_date else "",
        }
