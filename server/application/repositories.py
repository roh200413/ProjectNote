from server.domains.admin import AdminRepository
from server.domains.data_updates import DataUpdateRepository
from server.domains.projects import ProjectRepository
from server.domains.projects.models import Project
from server.domains.research_notes import ResearchNoteRepository
from server.domains.research_notes.models import ResearchNote
from server.domains.researchers import ResearcherRepository
from server.domains.researchers.models import Researcher
from server.domains.signatures import SignatureRepository


class WorkflowRepository:
    """Backward-compatible facade; prefer domain repositories directly."""

    def __init__(self) -> None:
        self.admin = AdminRepository()
        self.projects = ProjectRepository()
        self.researchers = ResearcherRepository()
        self.notes = ResearchNoteRepository()
        self.updates = DataUpdateRepository()
        self.signatures = SignatureRepository()

    def __getattr__(self, name: str):
        for repo in (self.admin, self.projects, self.researchers, self.notes, self.updates, self.signatures):
            if hasattr(repo, name):
                return getattr(repo, name)
        raise AttributeError(name)

    @staticmethod
    def dashboard_counts() -> dict:
        return {
            "projects": Project.objects.count(),
            "researchers": Researcher.objects.count(),
            "notes": ResearchNote.objects.count(),
        }

    @staticmethod
    def project_to_dict(project: Project) -> dict:
        return ProjectRepository.project_to_dict(project)


__all__ = ["WorkflowRepository"]
