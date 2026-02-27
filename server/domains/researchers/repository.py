from collections import defaultdict

from server.domains.admin.models import Team, UserAccount

def _as_text(value, default: str = "") -> str:
    if isinstance(value, list):
        value = value[0] if value else default
    if value is None:
        return default
    return str(value)


class ResearcherRepository:
    """Legacy-named repository backed by UserAccount (not Researcher model)."""

    def list_researchers(self) -> list[dict]:
        users = UserAccount.objects.select_related("team").order_by("id")
        return [
            {
                "id": user.id,
                "name": user.display_name,
                "role": "관리자" if user.role == UserAccount.Role.ADMIN else "연구원",
                "email": user.email,
                "organization": user.team.name if user.team else "미지정",
                "major": "미지정",
                "status": "활성",
            }
            for user in users
        ]

    def create_researcher(self, payload: dict) -> dict:
        email = _as_text(payload.get("email")).strip()
        if not email:
            raise ValueError("이메일은 필수입니다.")

        existing = UserAccount.objects.select_related("team").filter(email=email).first()
        if existing:
            return {
                "id": existing.id,
                "name": existing.display_name,
                "role": "관리자" if existing.role == UserAccount.Role.ADMIN else "연구원",
                "email": existing.email,
                "organization": existing.team.name if existing.team else "미지정",
                "major": "미지정",
                "status": "활성",
            }

        name = _as_text(payload.get("name"), "신규 연구원").strip()
        username_base = email.split("@")[0] or "user"
        username = username_base
        suffix = 1
        while UserAccount.objects.filter(username=username).exists():
            suffix += 1
            username = f"{username_base}{suffix}"

        team_name = _as_text(payload.get("organization")).strip()
        team = Team.objects.filter(name=team_name).first() if team_name else None

        created = UserAccount.objects.create(
            username=username,
            display_name=name,
            email=email,
            password="temp1234",
            role=UserAccount.Role.MEMBER,
            team=team,
        )

        return {
            "id": created.id,
            "name": created.display_name,
            "role": "연구원",
            "email": created.email,
            "organization": created.team.name if created.team else "미지정",
            "major": "미지정",
            "status": "활성",
        }

    def researcher_groups_for_selection(self) -> list[dict]:
        groups = []
        users = UserAccount.objects.select_related("team").order_by("team__name", "id")
        grouped = defaultdict(list)
        for user in users:
            organization = user.team.name if user.team else "미지정"
            grouped[organization].append(user)

        for org, members in grouped.items():
            groups.append(
                {
                    "group": f"{org} 연구그룹",
                    "lead": members[0].display_name,
                    "members": [{"id": m.id, "name": m.display_name, "organization": org} for m in members],
                }
            )
        return groups
