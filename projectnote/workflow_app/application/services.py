from projectnote.workflow_app.domains.projects.service import ProjectService


class WorkflowService(ProjectService):
    """Backward-compatible app service alias to domain-oriented project service."""
