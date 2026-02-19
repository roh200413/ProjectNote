import uuid

from django.db import models


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Team(TimestampedModel):
    name = models.CharField(max_length=120, unique=True)
    description = models.CharField(max_length=255, blank=True, default="")
    join_code = models.CharField(max_length=6, unique=True)


class AdminAccount(TimestampedModel):
    username = models.CharField(max_length=80, unique=True)
    display_name = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name="admin_accounts")
    is_super_admin = models.BooleanField(default=True)


class UserAccount(TimestampedModel):
    class Role(models.TextChoices):
        ADMIN = "admin", "관리자"
        MEMBER = "member", "일반"

    username = models.CharField(max_length=80, unique=True)
    display_name = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name="members")


class Researcher(TimestampedModel):
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    organization = models.CharField(max_length=255, default="미지정")
    major = models.CharField(max_length=255, default="미지정")
    status = models.CharField(max_length=50, default="활성")


class Project(TimestampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "draft"
        ACTIVE = "active", "active"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    manager = models.CharField(max_length=100, default="미지정")
    organization = models.CharField(max_length=255, default="미지정")
    code = models.CharField(max_length=100, blank=True, default="")
    description = models.TextField(blank=True, default="")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)


class ProjectMember(TimestampedModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="memberships")
    researcher = models.ForeignKey(Researcher, on_delete=models.CASCADE, related_name="project_memberships")
    role = models.CharField(max_length=100, default="member")
    contribution = models.CharField(max_length=255, default="프로젝트 참여")

    class Meta:
        unique_together = ("project", "researcher")


class ResearchNote(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="notes", null=True, blank=True)
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


class DataUpdate(TimestampedModel):
    target = models.CharField(max_length=255)
    status = models.CharField(max_length=50, default="queued")


class SignatureState(TimestampedModel):
    last_signed_by = models.CharField(max_length=100, default="")
    last_signed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, default="valid")
