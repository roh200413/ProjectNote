from projectnote.workflow_app.models import ResearchNote, ResearchNoteFile, ResearchNoteFolder


class ResearchNoteRepository:
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
