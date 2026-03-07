from __future__ import annotations

import hashlib
import re
from pathlib import Path


def _extract_hash(generated_ts: str) -> str | None:
    match = re.search(r"source_hash:([0-9a-f]{64})", generated_ts)
    return match.group(1) if match else None


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    openapi_file = root / "packages" / "types" / "generated" / "openapi.json"
    types_file = root / "packages" / "types" / "generated" / "api-types.ts"

    if not openapi_file.exists() or not types_file.exists():
        raise SystemExit("generated files are missing. run: python packages/types/scripts/generate_api_contract.py && python packages/types/scripts/generate_api_types.py")

    openapi_hash = hashlib.sha256(openapi_file.read_text().encode("utf-8")).hexdigest()
    generated_hash = _extract_hash(types_file.read_text())

    if generated_hash != openapi_hash:
        raise SystemExit(
            "type artifacts are stale. run generation scripts to refresh packages/types/generated/api-types.ts"
        )

    print("[packages/types] type artifacts are up-to-date")


if __name__ == "__main__":
    main()
