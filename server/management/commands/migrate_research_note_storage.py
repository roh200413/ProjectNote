import hashlib
import re
import shutil
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import OperationalError, ProgrammingError, transaction

from server.domains.research_notes.models import ResearchNote, ResearchNoteFile, ResearchNoteFolder
from server.domains.research_notes.storage_paths import (
    derived_assets_dir,
    derived_pages_dir,
    folder_relpath,
    source_images_dir,
    source_pdf_dir,
    storage_root,
)

_PAGE_PDF_RE = re.compile(r"_p\d{3}\.pdf$", re.IGNORECASE)
_IMAGE_FORMATS = {"jpeg", "jpg", "png", "svg", "tiff", "webp", "heif", "heic"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as src:
        for chunk in iter(lambda: src.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_new_layout_folder(note: ResearchNote, folder: Path) -> bool:
    token = f"/notebooks/{note.id}/"
    return token in str(folder).replace("\\", "/")


class Command(BaseCommand):
    help = "Migrate research-note files into standardized org/project/notebook storage layout."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Apply filesystem and DB changes. Default is dry-run.")
        parser.add_argument("--move", action="store_true", help="Move files instead of copy when --apply is set.")
        parser.add_argument(
            "--verify-hash-samples",
            type=int,
            default=10,
            help="Verify sha256 on up to N copied files (ignored with --move).",
        )
        parser.add_argument(
            "--archive-legacy",
            action="store_true",
            help="After apply+move, archive old legacy folders under _archive/legacy_research_notes/.",
        )
        parser.add_argument(
            "--fail-on-missing",
            action="store_true",
            help="Return non-zero exit when referenced files are missing.",
        )

    def handle(self, *args, **options):
        apply_changes = bool(options.get("apply"))
        move_files = bool(options.get("move")) and apply_changes
        verify_samples = max(int(options.get("verify_hash_samples") or 0), 0)
        archive_legacy = bool(options.get("archive_legacy")) and apply_changes and move_files
        fail_on_missing = bool(options.get("fail_on_missing"))
        archived_folders = 0

        total_notes = 0
        total_files = 0
        migrated_files = 0
        missing_files = 0
        hashed_files = 0
        hash_mismatch = 0

        if bool(options.get("archive_legacy")) and not (apply_changes and move_files):
            self.stdout.write(self.style.WARNING("--archive-legacy 는 --apply --move 와 함께만 동작합니다."))

        try:
            notes_qs = ResearchNote.objects.select_related("project", "project__company").order_by("updated_at")
            note_iter = list(notes_qs)
        except (OperationalError, ProgrammingError):
            self.stdout.write(self.style.WARNING("ResearchNote 테이블이 없습니다. 먼저 `python manage.py migrate`를 실행하세요."))
            return

        for note in note_iter:
            total_notes += 1
            folder_rows = list(ResearchNoteFolder.objects.filter(note=note).values_list("name", flat=True))
            source_folders = []
            for raw in folder_rows:
                base = Path(raw)
                if not base.is_absolute():
                    base = storage_root() / base
                source_folders.append(base)

            legacy_folders = [folder for folder in source_folders if not _is_new_layout_folder(note, folder)]
            used_dirs = set()
            for note_file in ResearchNoteFile.objects.filter(note=note).order_by("id"):
                total_files += 1
                filename = Path(note_file.name).name
                existing = next((folder / filename for folder in source_folders if (folder / filename).exists()), None)
                if existing is None:
                    missing_files += 1
                    continue

                fmt = str(note_file.format or "").lower().strip()
                if fmt == "pdf" and _PAGE_PDF_RE.search(filename):
                    target_dir = derived_pages_dir(note)
                elif fmt == "pdf":
                    target_dir = source_pdf_dir(note)
                elif fmt in _IMAGE_FORMATS:
                    target_dir = source_images_dir(note)
                else:
                    target_dir = derived_assets_dir(note)

                target_path = target_dir / filename
                used_dirs.add(target_dir)

                if apply_changes:
                    target_dir.mkdir(parents=True, exist_ok=True)
                    if existing.resolve() != target_path.resolve():
                        if move_files:
                            shutil.move(str(existing), str(target_path))
                        else:
                            shutil.copy2(existing, target_path)

                    if (not move_files) and verify_samples > 0 and hashed_files < verify_samples and target_path.exists():
                        hashed_files += 1
                        if _sha256(existing) != _sha256(target_path):
                            hash_mismatch += 1

                migrated_files += 1

            if apply_changes:
                desired_dirs = set(used_dirs)
                if not desired_dirs:
                    desired_dirs.update({source_pdf_dir(note), source_images_dir(note), derived_pages_dir(note)})
                    for path in desired_dirs:
                        path.mkdir(parents=True, exist_ok=True)

                with transaction.atomic():
                    ResearchNoteFolder.objects.filter(note=note).delete()
                    for path in sorted(desired_dirs, key=lambda p: str(p)):
                        ResearchNoteFolder.objects.create(note=note, name=folder_relpath(path))

                if archive_legacy:
                    archive_root = storage_root() / "_archive" / "legacy_research_notes" / str(note.id)
                    archive_root.mkdir(parents=True, exist_ok=True)
                    for folder in legacy_folders:
                        try:
                            if folder.exists() and folder.is_dir() and folder.resolve() not in {d.resolve() for d in desired_dirs}:
                                target = archive_root / folder.name
                                if target.exists():
                                    target = archive_root / f"{folder.name}_dup"
                                shutil.move(str(folder), str(target))
                                archived_folders += 1
                        except Exception:
                            continue

        mode = "APPLY" if apply_changes else "DRY-RUN"
        summary = f"[{mode}] notes={total_notes}, files={total_files}, migrated={migrated_files}, missing={missing_files}"
        if apply_changes and not move_files and verify_samples > 0:
            summary += f", hashed={hashed_files}, hash_mismatch={hash_mismatch}"
        if archive_legacy:
            summary += f", archived_folders={archived_folders}"
        if missing_files and fail_on_missing:
            self.stdout.write(self.style.ERROR(summary))
            raise SystemExit(2)
        self.stdout.write(self.style.SUCCESS(summary))
