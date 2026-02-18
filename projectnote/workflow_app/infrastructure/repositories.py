from collections import defaultdict
from datetime import datetime

from django.utils import timezone

from projectnote.workflow_app.domain import CreateProjectCommand, InvitedMemberCommand
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


class WorkflowRepository:
    def list_projects(self) -> list[dict]:
        return [self.project_to_dict(project) for project in Project.objects.order_by("-created_at")]

    def get_project(self, project_id: str) -> Project:
        return Project.objects.get(id=project_id)

    def create_project(self, command: CreateProjectCommand) -> Project:
        start_date = datetime.strptime(command.start_date, "%Y-%m-%d").date() if command.start_date else None
        end_date = datetime.strptime(command.end_date, "%Y-%m-%d").date() if command.end_date else None
        return Project.objects.create(
            name=command.name,
            manager=command.manager,
            organization=command.organization,
            code=command.code,
            description=command.description,
            start_date=start_date,
            end_date=end_date,
            status=command.status or Project.Status.DRAFT,
        )

    def create_project_members(self, project: Project, invited: list[InvitedMemberCommand]) -> None:
        ids = [item.researcher_id for item in invited]
        researchers = {researcher.id: researcher for researcher in Researcher.objects.filter(id__in=ids)}
        for item in invited:
            researcher = researchers.get(item.researcher_id)
            if not researcher:
                continue
            ProjectMember.objects.get_or_create(
                project=project,
                researcher=researcher,
                defaults={"role": item.role, "contribution": "프로젝트 참여"},
            )

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

    def list_research_notes(self) -> list[dict]:
        return [self.note_to_dict(note) for note in ResearchNote.objects.order_by("-updated_at")]

    def get_research_note(self, note_id: str) -> dict:
        note = ResearchNote.objects.get(id=note_id)
        return self.note_to_dict(note)

    def update_research_note(self, note_id: str, title: str | None, summary: str | None) -> dict:
        note = ResearchNote.objects.get(id=note_id)
        if title:
            note.title = title
        if summary:
            note.summary = summary
        note.save(update_fields=["title", "summary", "last_updated_at", "updated_at"])
        return self.note_to_dict(note)

    def list_note_files(self, note_id: str) -> list[dict]:
        return [
            {"id": str(f.id), "name": f.name, "author": f.author, "format": f.format, "created": f.created}
            for f in ResearchNoteFile.objects.filter(note_id=note_id).order_by("id")
        ]

    def list_note_folders(self, note_id: str) -> list[str]:
        return list(ResearchNoteFolder.objects.filter(note_id=note_id).order_by("id").values_list("name", flat=True))

    def create_data_update(self, payload: dict) -> dict:
        update = DataUpdate.objects.create(target=payload.get("target", "연구데이터"), status=payload.get("status", "queued"))
        return {"id": f"upd-{update.id}", "target": update.target, "status": update.status, "updated_at": update.updated_at.isoformat()}

    def list_data_updates(self) -> list[dict]:
        return [{"id": f"upd-{u.id}", "target": u.target, "status": u.status, "updated_at": u.updated_at.isoformat()} for u in DataUpdate.objects.order_by("-updated_at")]

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

    def project_note_ids(self, project_id: str) -> list[str]:
        return [str(i) for i in ResearchNote.objects.filter(project_id=project_id).values_list("id", flat=True)]

    def project_researcher_groups(self, project_id: str) -> list[dict]:
        memberships = ProjectMember.objects.filter(project_id=project_id).select_related("researcher")
        grouped = defaultdict(list)
        for member in memberships:
            grouped[member.researcher.organization].append(member)

        groups = []
        for organization, members in grouped.items():
            groups.append(
                {
                    "group": f"{organization} 연구그룹",
                    "lead": members[0].researcher.name,
                    "members": [
                        {
                            "name": m.researcher.name,
                            "role": m.role,
                            "organization": m.researcher.organization,
                            "major": m.researcher.major,
                            "contribution": m.contribution,
                        }
                        for m in members
                    ],
                }
            )
        return groups

    def dashboard_counts(self) -> dict:
        organization_count = Researcher.objects.values("organization").distinct().count()
        return {
            "organizations": organization_count,
            "projects": Project.objects.count(),
            "notes": ResearchNote.objects.count(),
            "revisions": 0,
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

    @staticmethod
    def project_to_dict(project: Project) -> dict:
        return {
            "id": str(project.id),
            "name": project.name,
            "status": project.status,
            "manager": project.manager,
            "organization": project.organization,
            "code": project.code,
            "description": project.description,
            "start_date": project.start_date.isoformat() if project.start_date else "",
            "end_date": project.end_date.isoformat() if project.end_date else "",
        }

    @staticmethod
    def note_to_dict(note: ResearchNote) -> dict:
        return {
            "id": str(note.id),
            "title": note.title,
            "owner": note.owner,
            "project_code": note.project_code,
            "period": note.period,
            "files": note.files,
            "members": note.members,
            "summary": note.summary,
            "last_updated_at": note.last_updated_at.isoformat() if note.last_updated_at else note.updated_at.isoformat(),
        }

    @staticmethod
    def signature_to_dict(signature: SignatureState) -> dict:
        return {
            "last_signed_by": signature.last_signed_by,
            "last_signed_at": signature.last_signed_at.isoformat() if signature.last_signed_at else "",
            "status": signature.status,
        }
