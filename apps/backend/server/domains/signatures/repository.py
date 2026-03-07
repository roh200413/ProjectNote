from django.utils import timezone

from server.domains.admin.models import UserAccount

from .models import SignatureState


class SignatureRepository:
    def get_or_create_signature_state(self, username: str) -> SignatureState | None:
        user = UserAccount.objects.filter(username=username).first()
        if not user:
            return None
        signature, _ = SignatureState.objects.get_or_create(
            user=user,
            defaults={"signature_data_url": "", "status": "valid"},
        )
        return signature

    def update_signature(self, username: str, status: str = "valid", signature_data_url: str = "") -> dict:
        signature = self.get_or_create_signature_state(username)
        if not signature:
            return {"last_signed_by": "", "last_signed_at": "", "status": status, "signature_data_url": ""}

        if signature_data_url:
            signature.signature_data_url = signature_data_url
        signature.status = status or signature.status
        signature.last_signed_at = timezone.now()
        signature.save(update_fields=["signature_data_url", "status", "last_signed_at", "updated_at"])
        return self.signature_to_dict(signature)

    def read_signature(self, username: str) -> dict:
        signature = self.get_or_create_signature_state(username)
        if not signature:
            return {"last_signed_by": "", "last_signed_at": "", "status": "valid", "signature_data_url": ""}
        return self.signature_to_dict(signature)

    @staticmethod
    def signature_to_dict(signature: SignatureState) -> dict:
        return {
            "last_signed_by": signature.user.display_name if signature.user else "",
            "last_signed_at": signature.last_signed_at.isoformat() if signature.last_signed_at else "",
            "status": signature.status,
            "signature_data_url": signature.signature_data_url,
        }
