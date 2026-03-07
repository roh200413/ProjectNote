from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


def _to_pascal(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", " ", value)
    return "".join(part.capitalize() for part in cleaned.split()) or "Unknown"


def _schema_to_ts(schema: dict) -> str:
    if "$ref" in schema:
        return schema["$ref"].split("/")[-1]

    t = schema.get("type")
    if t == "string":
        return "string"
    if t == "integer" or t == "number":
        return "number"
    if t == "boolean":
        return "boolean"
    if t == "array":
        return f"{_schema_to_ts(schema.get('items', {}))}[]"
    if t == "object":
        props = schema.get("properties", {})
        if not props:
            return "Record<string, unknown>"
        required = set(schema.get("required", []))
        fields = []
        for key, sub in props.items():
            optional = "" if key in required else "?"
            fields.append(f"  {key}{optional}: {_schema_to_ts(sub)};")
        return "{\n" + "\n".join(fields) + "\n}"
    return "unknown"


def _pick_success_schema(responses: dict) -> dict:
    preferred_codes = ["200", "201", "202", "204"]
    for code in preferred_codes:
        schema = (
            responses.get(code, {})
            .get("content", {})
            .get("application/json", {})
            .get("schema")
        )
        if schema:
            return schema

    for code, response in responses.items():
        if not str(code).startswith("2"):
            continue
        schema = response.get("content", {}).get("application/json", {}).get("schema")
        if schema:
            return schema

    return {"type": "object", "additionalProperties": True}


def main() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    source_path = repo_root / "packages" / "types" / "generated" / "openapi.json"
    target_path = repo_root / "packages" / "types" / "generated" / "api-types.ts"

    spec_text = source_path.read_text(encoding="utf-8")
    source_hash = hashlib.sha256(spec_text.encode("utf-8")).hexdigest()
    spec = json.loads(spec_text)

    lines: list[str] = []
    lines.append("/* AUTO-GENERATED FILE. DO NOT EDIT. */")
    lines.append(f"/* source_hash:{source_hash} */")
    lines.append("")

    schemas = spec.get("components", {}).get("schemas", {})
    for name, schema in schemas.items():
        lines.append(f"export type {name} = {_schema_to_ts(schema)};")
        lines.append("")

    paths = spec.get("paths", {})
    for path, operations in paths.items():
        for method, op in operations.items():
            op_name = op.get("operationId") or f"{method}_{path}"
            type_name = _to_pascal(op_name) + "Response"
            responses = op.get("responses", {})
            schema = _pick_success_schema(responses)
            lines.append(f"export type {type_name} = {_schema_to_ts(schema)};")

    target_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {target_path.relative_to(repo_root)}")


if __name__ == "__main__":
    main()
