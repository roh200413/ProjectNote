#!/usr/bin/env python
import os
import sys
from pathlib import Path


def main() -> None:
    # Repo root for module resolution and shared assets (.env, client/, storage/)
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.config.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
