import uuid

from django.db import models

from server.domains.common_models import TimestampedModel


class Project(TimestampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "draft"
        ACTIVE = "active", "active"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    manager = models.CharField(max_length=100, default="미지정")
    organization = models.CharField(max_length=255, default="미지정")
    company = models.ForeignKey("workflow_app.Team", on_delete=models.SET_NULL, null=True, blank=True, related_name="projects")
    code = models.CharField(max_length=100, blank=True, default="")
    description = models.TextField(blank=True, default="")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)


class ProjectMember(TimestampedModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="memberships")
    researcher = models.ForeignKey("workflow_app.Researcher", on_delete=models.CASCADE, related_name="project_memberships")
    role = models.CharField(max_length=100, default="member")
    contribution = models.CharField(max_length=255, default="프로젝트 참여")

    class Meta:
        unique_together = ("project", "researcher")
