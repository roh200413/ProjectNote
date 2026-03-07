from django.db import models

from server.domains.common_models import TimestampedModel


class DataUpdate(TimestampedModel):
    target = models.CharField(max_length=255)
    status = models.CharField(max_length=50, default="queued")
