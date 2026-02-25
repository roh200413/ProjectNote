from django.db import models

from server.domains.common_models import TimestampedModel


class SignatureState(TimestampedModel):
    last_signed_by = models.CharField(max_length=100, default="")
    last_signed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, default="valid")
