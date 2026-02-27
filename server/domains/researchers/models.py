from django.db import models

from server.domains.common_models import TimestampedModel


class Researcher(TimestampedModel):
    user = models.OneToOneField("workflow_app.UserAccount", on_delete=models.SET_NULL, null=True, blank=True, related_name="researcher_profile")
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    organization = models.CharField(max_length=255, default="미지정")
    major = models.CharField(max_length=255, default="미지정")
    status = models.CharField(max_length=50, default="활성")
