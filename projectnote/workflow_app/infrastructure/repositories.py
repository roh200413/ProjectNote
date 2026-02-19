from projectnote.workflow_app.domains.admin import AdminRepository
from projectnote.workflow_app.domains.dashboard import DashboardService
from projectnote.workflow_app.domains.data_updates import DataUpdateRepository
from projectnote.workflow_app.domains.projects import (
    CreateProjectCommand,
    InvitedMemberCommand,
    ProjectRepository,
)
from projectnote.workflow_app.domains.research_notes import ResearchNoteRepository
from projectnote.workflow_app.domains.researchers import ResearcherRepository
from projectnote.workflow_app.domains.signatures import SignatureRepository
from projectnote.workflow_app.models import Project


class WorkflowRepository:
    """Facade repository kept for backward compatibility with existing views."""

    def __init__(self) -> None:
        self.admin = AdminRepository()
        self.projects = ProjectRepository()
        self.researchers = ResearcherRepository()
        self.notes = ResearchNoteRepository()
        self.updates = DataUpdateRepository()
        self.signatures = SignatureRepository()


    def list_teams(self) -> list[dict]:
        return self.admin.list_teams()

    def create_team(self, name: str, description: str) -> dict:
        return self.admin.create_team(name, description)

    def list_admin_accounts(self) -> list[dict]:
        return self.admin.list_admin_accounts()

    def find_user_for_login(self, username: str, password: str) -> dict | None:
        return self.admin.find_user_for_login(username, password)

    def find_super_admin_for_login(self, username: str, password: str) -> dict | None:
        return self.admin.find_super_admin_for_login(username, password)

    def register_user(
        self,
        username: str,
        display_name: str,
        email: str,
        password: str,
        role: str,
        team_name: str,
        team_description: str,
        team_code: str,
    ) -> dict:
        return self.admin.register_user(
            username=username,
            display_name=display_name,
            email=email,
            password=password,
            role=role,
            team_name=team_name,
            team_description=team_description,
            team_code=team_code,
        )

    def list_all_users(self, keyword: str = "") -> list[dict]:
        return self.admin.list_all_users(keyword)

    def assign_user_team(self, user_id: int, team_id: int | None) -> dict:
        return self.admin.assign_user_team(user_id, team_id)

    def create_initial_admin(self, username: str, display_name: str, email: str, password: str, team_id: str | None) -> dict:
        return self.admin.create_initial_admin(username, display_name, email, password, team_id)

    def list_managed_tables(self) -> list[dict]:
        return self.admin.list_managed_tables()

    def truncate_table(self, table_name: str) -> None:
        self.admin.truncate_table(table_name)

    def list_projects(self) -> list[dict]:
        return self.projects.list_projects()

    def get_project(self, project_id: str) -> Project:
        return self.projects.get_project(project_id)

    def create_project(self, command: CreateProjectCommand) -> Project:
        return self.projects.create_project(command)

    def create_project_members(self, project: Project, invited: list[InvitedMemberCommand]) -> None:
        self.projects.create_project_members(project, invited)

    def list_researchers(self) -> list[dict]:
        return self.researchers.list_researchers()

    def create_researcher(self, payload: dict) -> dict:
        return self.researchers.create_researcher(payload)

    def list_research_notes(self) -> list[dict]:
        return self.notes.list_research_notes()

    def get_research_note(self, note_id: str) -> dict:
        return self.notes.get_research_note(note_id)

    def update_research_note(self, note_id: str, title: str | None, summary: str | None) -> dict:
        return self.notes.update_research_note(note_id, title, summary)

    def list_note_files(self, note_id: str) -> list[dict]:
        return self.notes.list_note_files(note_id)

    def list_note_folders(self, note_id: str) -> list[str]:
        return self.notes.list_note_folders(note_id)

    def create_data_update(self, payload: dict) -> dict:
        return self.updates.create_data_update(payload)

    def list_data_updates(self) -> list[dict]:
        return self.updates.list_data_updates()

    def update_signature(self, signed_by: str, status: str) -> dict:
        return self.signatures.update_signature(signed_by, status)

    def read_signature(self) -> dict:
        return self.signatures.read_signature()

    def project_note_ids(self, project_id: str) -> list[str]:
        return self.projects.project_note_ids(project_id)

    def project_researcher_groups(self, project_id: str) -> list[dict]:
        return self.projects.project_researcher_groups(project_id)

    def dashboard_counts(self) -> dict:
        return DashboardService.counts()

    def researcher_groups_for_selection(self) -> list[dict]:
        return self.researchers.researcher_groups_for_selection()

    @staticmethod
    def project_to_dict(project: Project) -> dict:
        return ProjectRepository.project_to_dict(project)
