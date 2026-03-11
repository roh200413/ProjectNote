from django.db import OperationalError, ProgrammingError

from .models import ResearchNote, ResearchNoteFile, ResearchNoteFolder


class ResearchNoteRepository:
    _NOTE_VALUES_FIELDS = (
        "id",
        "title",
        "owner",
        "project_code",
        "period",
        "files",
        "members",
        "summary",
        "last_updated_at",
        "updated_at",
    )

    def _note_row_to_dict(self, row: dict, *, show_title: bool = True) -> dict:
        return {
            "id": str(row["id"]),
            "title": row["title"],
            "owner": row["owner"],
            "project_code": row["project_code"],
            "period": row["period"],
            "files": row["files"],
            "members": row["members"],
            "summary": row["summary"],
            "show_title": bool(show_title),
            "last_updated_at": row["last_updated_at"].isoformat() if row["last_updated_at"] else row["updated_at"].isoformat(),
        }

    def _fallback_list_research_notes(self) -> list[dict]:
        rows = ResearchNote.objects.order_by("-updated_at").values(*self._NOTE_VALUES_FIELDS)
        return [self._note_row_to_dict(row, show_title=True) for row in rows]

    def _fallback_get_research_note(self, note_id: str) -> dict:
        row = ResearchNote.objects.values(*self._NOTE_VALUES_FIELDS).get(id=note_id)
        return self._note_row_to_dict(row, show_title=True)

    def list_research_notes(self) -> list[dict]:
        try:
            return [self.note_to_dict(note) for note in ResearchNote.objects.order_by("-updated_at")]
        except (OperationalError, ProgrammingError):
            # Backward compatibility for DBs that haven't applied show_title migration yet.
            return self._fallback_list_research_notes()

    def get_research_note(self, note_id: str) -> dict:
        try:
            note = ResearchNote.objects.get(id=note_id)
            return self.note_to_dict(note)
        except (OperationalError, ProgrammingError):
            return self._fallback_get_research_note(note_id)

    def update_research_note(self, note_id: str, title: str | None, summary: str | None, show_title: bool | None = None) -> dict:
        try:
            note = ResearchNote.objects.get(id=note_id)
            if title:
                note.title = title
            if summary:
                note.summary = summary
            if show_title is not None:
                note.show_title = bool(show_title)
            note.save(update_fields=["title", "summary", "show_title", "last_updated_at", "updated_at"])
            return self.note_to_dict(note)
        except (OperationalError, ProgrammingError):
            updates = {}
            if title:
                updates["title"] = title
            if summary:
                updates["summary"] = summary
            if updates:
                ResearchNote.objects.filter(id=note_id).update(**updates)
            return self._fallback_get_research_note(note_id)

    def list_note_files(self, note_id: str) -> list[dict]:
        return [
            {"id": str(f.id), "name": f.name, "author": f.author, "format": f.format, "created": f.created}
            for f in ResearchNoteFile.objects.filter(note_id=note_id).order_by("id")
        ]

    def list_note_folders(self, note_id: str) -> list[str]:
        return list(ResearchNoteFolder.objects.filter(note_id=note_id).order_by("id").values_list("name", flat=True))

    def get_note_file(self, note_id: str, file_id: str) -> dict:
        file = ResearchNoteFile.objects.get(id=file_id, note_id=note_id)
        return {"id": str(file.id), "name": file.name, "author": file.author, "format": file.format, "created": file.created}

    def update_note_file(self, note_id: str, file_id: str, author: str | None, created: str | None) -> dict:
        file = ResearchNoteFile.objects.get(id=file_id, note_id=note_id)
        if author is not None:
            file.author = author.strip() or file.author
        if created is not None:
            file.created = created.strip() or file.created
        file.save(update_fields=["author", "created", "updated_at"])
        return {"id": str(file.id), "name": file.name, "author": file.author, "format": file.format, "created": file.created}

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
            "show_title": bool(note.show_title),
            "last_updated_at": note.last_updated_at.isoformat() if note.last_updated_at else note.updated_at.isoformat(),
        }
