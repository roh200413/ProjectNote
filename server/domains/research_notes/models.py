import uuid

from django.db import models

from server.domains.common_models import TimestampedModel


class ResearchNote(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey("workflow_app.Project", on_delete=models.CASCADE, related_name="notes", null=True, blank=True)
    title = models.CharField(max_length=255)
    owner = models.CharField(max_length=100)
    project_code = models.CharField(max_length=100, blank=True, default="")
    period = models.CharField(max_length=100, blank=True, default="")
    files = models.PositiveIntegerField(default=0)
    members = models.PositiveIntegerField(default=0)
    summary = models.TextField(blank=True, default="")
    last_updated_at = models.DateTimeField(auto_now=True)


class ResearchNoteFile(TimestampedModel):
    note = models.ForeignKey(ResearchNote, on_delete=models.CASCADE, related_name="note_files")
    name = models.CharField(max_length=255)
    author = models.CharField(max_length=100)
    format = models.CharField(max_length=20)
    created = models.CharField(max_length=100)


class ResearchNoteFolder(TimestampedModel):
    note = models.ForeignKey(ResearchNote, on_delete=models.CASCADE, related_name="folders")
    name = models.CharField(max_length=255)
