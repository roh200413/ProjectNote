from django.db import models

from server.domains.common_models import TimestampedModel


class Team(TimestampedModel):
    name = models.CharField(max_length=120, unique=True)
    description = models.CharField(max_length=255, blank=True, default="")
    join_code = models.CharField(max_length=6, unique=True)

    class Meta:
        db_table = "workflow_app_company"


class SuperAdminAccount(TimestampedModel):
    username = models.CharField(max_length=80, unique=True)
    display_name = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    organization = models.CharField(max_length=255, default="ProjectNote")
    major = models.CharField(max_length=255, default="관리")
    is_active = models.BooleanField(default=True)


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
