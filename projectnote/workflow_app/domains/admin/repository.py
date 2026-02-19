from django.db import connection

from projectnote.workflow_app.models import AdminAccount, Team


class AdminRepository:
    MANAGED_TABLES = [
        "workflow_app_team",
        "workflow_app_adminaccount",
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
                "created_at": team.created_at.isoformat(),
            }
            for team in Team.objects.order_by("id")
        ]

    def create_team(self, name: str, description: str) -> dict:
        team = Team.objects.create(name=name, description=description)
        return {"id": team.id, "name": team.name, "description": team.description}

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
