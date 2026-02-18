from projectnote.workflow_app.models import Project, ResearchNote, Researcher


class DashboardService:
    @staticmethod
    def counts() -> dict:
        organization_count = Researcher.objects.values("organization").distinct().count()
        return {
            "organizations": organization_count,
            "projects": Project.objects.count(),
            "notes": ResearchNote.objects.count(),
            "revisions": 0,
        }
