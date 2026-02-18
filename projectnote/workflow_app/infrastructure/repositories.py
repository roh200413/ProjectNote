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
        self.projects = ProjectRepository()
        self.researchers = ResearcherRepository()
        self.notes = ResearchNoteRepository()
        self.updates = DataUpdateRepository()
        self.signatures = SignatureRepository()

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
