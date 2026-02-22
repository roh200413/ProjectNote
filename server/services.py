from server.features.projects.service import ProjectService


class WorkflowService(ProjectService):
    """Project use-case service facade."""


__all__ = ["WorkflowService"]
