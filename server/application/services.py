from server.domains.projects.service import ProjectService


class WorkflowService(ProjectService):
    """Project use-case service facade."""


__all__ = ["WorkflowService"]
