from projectnote.workflow_app.models import DataUpdate


class DataUpdateRepository:
    def create_data_update(self, payload: dict) -> dict:
        update = DataUpdate.objects.create(target=payload.get("target", "연구데이터"), status=payload.get("status", "queued"))
        return {"id": f"upd-{update.id}", "target": update.target, "status": update.status, "updated_at": update.updated_at.isoformat()}

    def list_data_updates(self) -> list[dict]:
        return [{"id": f"upd-{u.id}", "target": u.target, "status": u.status, "updated_at": u.updated_at.isoformat()} for u in DataUpdate.objects.order_by("-updated_at")]
