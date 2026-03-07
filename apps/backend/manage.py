#!/usr/bin/env python
import os
import sys
from pathlib import Path


def _should_auto_migrate(argv: list[str]) -> bool:
    if len(argv) < 2:
        return False
    command = argv[1]
    if command != "runserver":
        return False
    return "--skip-migrate" not in argv


def _without_skip_migrate(argv: list[str]) -> list[str]:
    return [arg for arg in argv if arg != "--skip-migrate"]


def main() -> None:
    # Repo root for module resolution and shared assets (.env, client/, storage/)
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.config.settings")

    from django.core.management import execute_from_command_line

    argv = _without_skip_migrate(sys.argv)
    if _should_auto_migrate(argv):
        execute_from_command_line([argv[0], "migrate", "--noinput"])

    execute_from_command_line(argv)


if __name__ == "__main__":
    main()
