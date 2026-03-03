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
                "username": user.username,
                "name": user.display_name,
                "role": (
                    "소유자"
                    if user.role == UserAccount.Role.OWNER
                    else "관리자" if user.role == UserAccount.Role.ADMIN else "연구원"
                ),
                "email": user.email,
                "organization": user.team.name if user.team else "미지정",
                "team_id": user.team_id,
                "major": "미지정",
                "status": "승인" if user.is_approved else "승인대기",
                "is_approved": user.is_approved,
            }
            for user in users
        ]

    def list_teams(self) -> list[dict]:
        return [{"id": team.id, "name": team.name} for team in Team.objects.order_by("name", "id")]

    def create_researcher(self, payload: dict) -> dict:
        email = _as_text(payload.get("email")).strip()
        if not email:
            raise ValueError("이메일은 필수입니다.")

        existing = UserAccount.objects.select_related("team").filter(email=email).first()
        if existing:
            return {
                "id": existing.id,
                "username": existing.username,
                "name": existing.display_name,
                "role": (
                    "소유자"
                    if existing.role == UserAccount.Role.OWNER
                    else "관리자" if existing.role == UserAccount.Role.ADMIN else "연구원"
                ),
                "email": existing.email,
                "organization": existing.team.name if existing.team else "미지정",
                "team_id": existing.team_id,
                "major": "미지정",
                "status": "승인" if existing.is_approved else "승인대기",
                "is_approved": existing.is_approved,
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
            is_approved=False,
        )

        return {
            "id": created.id,
            "username": created.username,
            "name": created.display_name,
            "role": "연구원",
            "email": created.email,
            "organization": created.team.name if created.team else "미지정",
            "team_id": created.team_id,
            "major": "미지정",
            "status": "승인대기",
            "is_approved": created.is_approved,
        }

    def approve_user(self, user_id: int) -> dict:
        user = UserAccount.objects.select_related("team").filter(id=user_id).first()
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다.")
        if not user.team_id:
            raise ValueError("회사(팀) 지정 후 승인할 수 있습니다.")
        user.is_approved = True
        user.save(update_fields=["is_approved", "updated_at"])
        return {"id": user.id, "status": "승인", "is_approved": True}

    def grant_role(self, user_id: int, role: str) -> dict:
        user = UserAccount.objects.filter(id=user_id).first()
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다.")
        if role not in {UserAccount.Role.ADMIN, UserAccount.Role.MEMBER}:
            raise ValueError("권한 값이 올바르지 않습니다.")
        user.role = role
        user.save(update_fields=["role", "updated_at"])
        return {"id": user.id, "role": user.get_role_display()}

    def assign_team(self, user_id: int, team_id: int | None) -> dict:
        user = UserAccount.objects.select_related("team").filter(id=user_id).first()
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다.")
        team = None
        if team_id is not None:
            team = Team.objects.filter(id=team_id).first()
            if not team:
                raise ValueError("팀을 찾을 수 없습니다.")
        user.team = team
        user.save(update_fields=["team", "updated_at"])
        return {"id": user.id, "team": user.team.name if user.team else "미지정"}

    def expel_user(self, user_id: int) -> dict:
        user = UserAccount.objects.filter(id=user_id).first()
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다.")
        username = user.username
        user.delete()
        return {"username": username}

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
