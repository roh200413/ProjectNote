from django.db import models

from server.domains.common_models import TimestampedModel


class SignatureState(TimestampedModel):
    user = models.OneToOneField("workflow_app.UserAccount", on_delete=models.CASCADE, related_name="signature_state", null=True, blank=True)
    signature_data_url = models.TextField(blank=True, default="")
    last_signed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, default="valid")
