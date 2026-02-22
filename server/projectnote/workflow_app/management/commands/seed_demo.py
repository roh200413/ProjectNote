from django.core.management.base import BaseCommand
from django.utils import timezone

from projectnote.workflow_app.models import (
    DataUpdate,
    Project,
    ProjectMember,
    ResearchNote,
    ResearchNoteFile,
    ResearchNoteFolder,
    Researcher,
    SignatureState,
)


class Command(BaseCommand):
    help = "워크플로우 화면 확인용 데모 데이터를 생성합니다."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="생성 전에 workflow_app 데이터를 초기화합니다.",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            ProjectMember.objects.all().delete()
            ResearchNoteFile.objects.all().delete()
            ResearchNoteFolder.objects.all().delete()
            ResearchNote.objects.all().delete()
            Project.objects.all().delete()
            Researcher.objects.all().delete()
            DataUpdate.objects.all().delete()
            SignatureState.objects.all().delete()

        researcher1, _ = Researcher.objects.get_or_create(
            email="kim@example.com",
            defaults={
                "name": "김기수",
                "role": "PI",
                "organization": "딥테크딥스",
                "major": "R&D",
                "status": "활성",
            },
        )
        researcher2, _ = Researcher.objects.get_or_create(
            email="choi@example.com",
            defaults={
                "name": "최재혁",
                "role": "연구원",
                "organization": "ProjectNote Lab",
                "major": "프론트엔드",
                "status": "활성",
            },
        )

        project, _ = Project.objects.get_or_create(
            code="PN-DEMO-001",
            defaults={
                "name": "ProjectNote 데모 프로젝트",
                "status": "active",
                "manager": "노승희",
                "organization": "ProjectNote Lab",
                "description": "DB 확인 및 화면 데모용 샘플 프로젝트",
            },
        )

        ProjectMember.objects.get_or_create(
            project=project,
            researcher=researcher1,
            defaults={"role": "admin", "contribution": "연구 총괄"},
        )
        ProjectMember.objects.get_or_create(
            project=project,
            researcher=researcher2,
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
            id=1,
            defaults={
                "last_signed_by": "노승희",
                "last_signed_at": timezone.now(),
                "status": "valid",
            },
        )

        self.stdout.write(self.style.SUCCESS("데모 데이터 생성 완료"))
