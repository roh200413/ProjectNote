from collections import defaultdict

from django.utils import timezone

from projectnote.workflow_app.models import Researcher


class ResearcherRepository:
    def list_researchers(self) -> list[dict]:
        return [
            {
                "id": str(r.id),
                "name": r.name,
                "role": r.role,
                "email": r.email,
                "organization": r.organization,
                "major": r.major,
                "status": r.status,
            }
            for r in Researcher.objects.order_by("id")
        ]

    def create_researcher(self, payload: dict) -> dict:
        researcher = Researcher.objects.create(
            name=payload.get("name", "신규 연구원"),
            role=payload.get("role", "연구원"),
            email=payload.get("email", f"unknown-{timezone.now().timestamp()}@example.com"),
            organization=payload.get("organization", "미지정"),
            major=payload.get("major", "미지정"),
            status="활성",
        )
        return {
            "id": str(researcher.id),
            "name": researcher.name,
            "role": researcher.role,
            "email": researcher.email,
            "organization": researcher.organization,
            "major": researcher.major,
            "status": researcher.status,
        }

    def researcher_groups_for_selection(self) -> list[dict]:
        groups = []
        researchers = Researcher.objects.order_by("organization", "id")
        grouped = defaultdict(list)
        for researcher in researchers:
            grouped[researcher.organization].append(researcher)

        for org, members in grouped.items():
            groups.append(
                {
                    "group": f"{org} 연구그룹",
                    "lead": members[0].name,
                    "members": [{"id": str(m.id), "name": m.name, "organization": m.organization} for m in members],
                }
            )
        return groups
