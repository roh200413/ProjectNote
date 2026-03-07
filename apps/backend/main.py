import os
import sys
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.config.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(["manage.py", "runserver", "127.0.0.1:8000"])


if __name__ == "__main__":
    main()
