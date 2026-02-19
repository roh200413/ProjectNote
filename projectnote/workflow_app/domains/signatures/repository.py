from django.utils import timezone

from projectnote.workflow_app.models import SignatureState


class SignatureRepository:
    def get_or_create_signature_state(self) -> SignatureState:
        signature, _ = SignatureState.objects.get_or_create(id=1, defaults={"last_signed_by": "", "status": "valid"})
        return signature

    def update_signature(self, signed_by: str, status: str) -> dict:
        signature = self.get_or_create_signature_state()
        signature.last_signed_by = signed_by or signature.last_signed_by
        signature.status = status or signature.status
        signature.last_signed_at = timezone.now()
        signature.save(update_fields=["last_signed_by", "status", "last_signed_at", "updated_at"])
        return self.signature_to_dict(signature)

    def read_signature(self) -> dict:
        return self.signature_to_dict(self.get_or_create_signature_state())

    @staticmethod
    def signature_to_dict(signature: SignatureState) -> dict:
        return {
            "last_signed_by": signature.last_signed_by,
            "last_signed_at": signature.last_signed_at.isoformat() if signature.last_signed_at else "",
            "status": signature.status,
        }
