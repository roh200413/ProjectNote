from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(repo_root))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.config.settings")

    import django

    django.setup()

    from server.application.openapi import build_openapi_spec

    out_file = repo_root / "packages" / "types" / "generated" / "openapi.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(build_openapi_spec(), ensure_ascii=False, indent=2) + "\n")
    print(f"wrote {out_file.relative_to(repo_root)}")


if __name__ == "__main__":
    main()
