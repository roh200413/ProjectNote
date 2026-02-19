import random
import string

from django.db import connection
from django.db.models import Q

from projectnote.workflow_app.models import AdminAccount, SuperAdminAccount, Team, UserAccount


class AdminRepository:
    MANAGED_TABLES = [
        "workflow_app_team",
        "workflow_app_adminaccount",
        "workflow_app_superadminaccount",
        "workflow_app_useraccount",
        "workflow_app_project",
        "workflow_app_researcher",
        "workflow_app_projectmember",
        "workflow_app_researchnote",
        "workflow_app_researchnotefile",
        "workflow_app_researchnotefolder",
        "workflow_app_dataupdate",
        "workflow_app_signaturestate",
        "django_session",
    ]

    def list_teams(self) -> list[dict]:
        return [
            {
                "id": team.id,
                "name": team.name,
                "description": team.description,
                "join_code": team.join_code,
                "created_at": team.created_at.isoformat(),
            }
            for team in Team.objects.order_by("id")
        ]

    def create_team(self, name: str, description: str) -> dict:
        team = Team.objects.create(name=name, description=description, join_code=self._generate_join_code())
        return {"id": team.id, "name": team.name, "description": team.description, "join_code": team.join_code}

    def _generate_join_code(self) -> str:
        for _ in range(30):
            code = "".join(random.choices(string.digits, k=6))
            if not Team.objects.filter(join_code=code).exists():
                return code
        raise ValueError("팀 코드 생성에 실패했습니다. 다시 시도해주세요.")

    def list_admin_accounts(self) -> list[dict]:
        return [
            {
                "id": admin.id,
                "username": admin.username,
                "display_name": admin.display_name,
                "email": admin.email,
                "team": admin.team.name if admin.team else "-",
                "is_super_admin": admin.is_super_admin,
            }
            for admin in AdminAccount.objects.select_related("team").order_by("id")
        ]

    def find_user_for_login(self, username: str, password: str) -> dict | None:
        user = UserAccount.objects.select_related("team").filter(username=username, password=password).first()
        if not user:
            return None
        return {
            "username": user.username,
            "name": user.display_name,
            "role": "관리자" if user.role == UserAccount.Role.ADMIN else "일반",
            "email": user.email,
            "organization": user.team.name if user.team else "미지정",
            "major": "미지정",
            "team": user.team.name if user.team else "-",
        }

    def find_super_admin_for_login(self, username: str, password: str) -> dict | None:
        account = SuperAdminAccount.objects.filter(
            username=username,
            password=password,
            is_active=True,
        ).first()
        if not account:
            return None
        return {
            "username": account.username,
            "name": account.display_name,
            "role": "슈퍼관리자",
            "email": account.email,
            "organization": account.organization,
            "major": account.major,
            "team": "SUPER_ADMIN",
            "is_super_admin": True,
        }

    def list_all_users(self, keyword: str = "") -> list[dict]:
        users = UserAccount.objects.select_related("team")
        if keyword:
            users = users.filter(
                Q(username__icontains=keyword)
                | Q(display_name__icontains=keyword)
                | Q(email__icontains=keyword)
                | Q(team__name__icontains=keyword)
            )

        return [
            {
                "id": user.id,
                "username": user.username,
                "display_name": user.display_name,
                "email": user.email,
                "role": user.get_role_display(),
                "team": user.team.name if user.team else "-",
                "join_code": user.team.join_code if user.team else "-",
            }
            for user in users.distinct().order_by("id")
        ]

    def assign_user_team(self, user_id: int, team_id: int | None) -> dict:
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
        return {
            "id": user.id,
            "username": user.username,
            "team": user.team.name if user.team else "-",
            "join_code": user.team.join_code if user.team else "-",
        }

    def register_user(
        self,
        username: str,
        display_name: str,
        email: str,
        password: str,
        role: str,
        team_name: str,
        team_description: str,
        team_code: str,
    ) -> dict:
        normalized_role = role if role in {UserAccount.Role.ADMIN, UserAccount.Role.MEMBER} else UserAccount.Role.MEMBER
        if UserAccount.objects.filter(username=username).exists():
            raise ValueError("이미 사용 중인 아이디입니다.")
        if UserAccount.objects.filter(email=email).exists():
            raise ValueError("이미 사용 중인 이메일입니다.")

        team = None
        if normalized_role == UserAccount.Role.ADMIN:
            if not team_name:
                raise ValueError("관리자 가입 시 팀 이름은 필수입니다.")
            team = Team.objects.create(
                name=team_name,
                description=team_description,
                join_code=self._generate_join_code(),
            )
        elif team_name or team_code:
            team = Team.objects.filter(name=team_name, join_code=team_code).first()
            if not team:
                raise ValueError("팀 이름 또는 팀 코드가 올바르지 않습니다.")

        user = UserAccount.objects.create(
            username=username,
            display_name=display_name,
            email=email,
            password=password,
            role=normalized_role,
            team=team,
        )
        return {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "email": user.email,
            "role": user.get_role_display(),
            "team": team.name if team else "-",
            "join_code": team.join_code if team else "-",
        }

    def create_initial_admin(self, username: str, display_name: str, email: str, password: str, team_id: str | None) -> dict:
        if AdminAccount.objects.exists():
            raise ValueError("최초 관리자 계정은 이미 생성되었습니다.")

        team = Team.objects.filter(id=team_id).first() if team_id else None
        admin = AdminAccount.objects.create(
            username=username,
            display_name=display_name,
            email=email,
            password=password,
            team=team,
            is_super_admin=True,
        )
        return {
            "id": admin.id,
            "username": admin.username,
            "display_name": admin.display_name,
            "email": admin.email,
            "team": admin.team.name if admin.team else "-",
            "is_super_admin": admin.is_super_admin,
        }

    def list_managed_tables(self) -> list[dict]:
        rows = []
        with connection.cursor() as cursor:
            for table_name in self.MANAGED_TABLES:
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=%s",
                    [table_name],
                )
                if not cursor.fetchone():
                    continue
                cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
                count = cursor.fetchone()[0]
                rows.append({"table": table_name, "rows": count})
        return rows

    def truncate_table(self, table_name: str) -> None:
        if table_name not in self.MANAGED_TABLES:
            raise ValueError("관리 대상이 아닌 테이블입니다.")

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=%s",
                [table_name],
            )
            if not cursor.fetchone():
                raise ValueError("테이블이 존재하지 않습니다.")
            if table_name == "workflow_app_team":
                cursor.execute('DELETE FROM "workflow_app_adminaccount" WHERE team_id IS NOT NULL')
            cursor.execute(f'DELETE FROM "{table_name}"')
