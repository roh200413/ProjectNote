from django.utils import timezone

from server.domains.admin.models import Team, UserAccount
from server.domains.data_updates.models import DataUpdate
from server.domains.projects.models import Project, ProjectMember
from server.domains.research_notes.models import ResearchNote, ResearchNoteFile, ResearchNoteFolder
from server.domains.signatures.models import SignatureState


def seed_demo_data(reset: bool = False) -> dict[str, int]:
    """Create deterministic mock data without relying on management commands."""
    if reset:
        ProjectMember.objects.all().delete()
        ResearchNoteFile.objects.all().delete()
        ResearchNoteFolder.objects.all().delete()
        ResearchNote.objects.all().delete()
        Project.objects.all().delete()
        DataUpdate.objects.all().delete()
        SignatureState.objects.all().delete()
        UserAccount.objects.all().delete()
        Team.objects.all().delete()

    team1, _ = Team.objects.get_or_create(name="딥테크딥스", defaults={"description": "R&D 팀", "join_code": "100001"})
    team2, _ = Team.objects.get_or_create(name="ProjectNote Lab", defaults={"description": "Product 팀", "join_code": "100002"})

    user1, _ = UserAccount.objects.get_or_create(
        email="kim@example.com",
        defaults={
            "username": "kim",
            "display_name": "김기수",
            "password": "secret123",
            "role": UserAccount.Role.ADMIN,
            "team": team1,
        },
    )
    user2, _ = UserAccount.objects.get_or_create(
        email="choi@example.com",
        defaults={
            "username": "choi",
            "display_name": "최재혁",
            "password": "secret123",
            "role": UserAccount.Role.MEMBER,
            "team": team2,
        },
    )

    project, _ = Project.objects.get_or_create(
        code="PN-DEMO-001",
        defaults={
            "name": "ProjectNote 데모 프로젝트",
            "status": "active",
            "manager": "노승희",
            "organization": "ProjectNote Lab",
            "company": team2,
            "description": "DB 확인 및 화면 데모용 샘플 프로젝트",
        },
    )

    ProjectMember.objects.get_or_create(
        project=project,
        user=user1,
        defaults={"role": "admin", "contribution": "연구 총괄"},
    )
    ProjectMember.objects.get_or_create(
        project=project,
        user=user2,
        defaults={"role": "member", "contribution": "UI/뷰어 개발"},
    )

    note, _ = ResearchNote.objects.get_or_create(
        project=project,
        title="데모 연구노트",
        defaults={
            "owner": "노승희",
            "project_code": project.code,
            "period": "2026.01.01 ~ 2026.12.31",
            "files": 1,
            "members": 2,
            "summary": "데모 데이터로 생성된 연구노트입니다.",
        },
    )

    ResearchNoteFile.objects.get_or_create(
        note=note,
        name="demo-file.pdf",
        defaults={"author": "노승희", "format": "pdf", "created": "2026.02.01 / 10:00 AM"},
    )
    ResearchNoteFolder.objects.get_or_create(note=note, name="[DEMO - DOCS]")

    DataUpdate.objects.get_or_create(target="연구노트 메타데이터", defaults={"status": "completed"})

    SignatureState.objects.update_or_create(
        user=user1,
        defaults={
            "signature_data_url": "",
            "last_signed_at": timezone.now(),
            "status": "valid",
        },
    )

    return {
        "projects": Project.objects.count(),
        "researchers": UserAccount.objects.count(),
        "notes": ResearchNote.objects.count(),
    }
