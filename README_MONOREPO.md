# ProjectNote Monorepo Skeleton (Step 1)

This repository now includes a **non-invasive monorepo skeleton**.
Existing Django code remains in place; no legacy files were moved.

## Directory layout

- `apps/backend` — future backend app workspace (Django relocation target)
- `apps/web` — future frontend app workspace
- `packages/ui` — shared UI package workspace
- `packages/types` — shared API/domain types workspace
- `tooling` — root tooling scripts (run/check/lint entrypoints)

## Quick commands

From repository root:

- `./tooling/scripts/run_backend.sh` (Django check via `apps/backend/manage.py`)
- `./tooling/scripts/run_web.sh`
- `./tooling/scripts/check_ui.sh`
- `./tooling/scripts/check_types.sh`
- `./tooling/scripts/generate_api_types.sh`
- `./tooling/scripts/lint_repo.sh`
- `./tooling/scripts/qa_smoke.sh`

## Notes

- This step only creates the skeleton and executable stubs.
- Core `/api/v1/*` backend APIs remain stable; `/frontend/*` template routes are in cutover mode and redirect to `apps/web`.
- Next steps can migrate code incrementally into these folders.

- Frontend cutover mapping (phase 3): `apps/web/docs/cutover-phase3-mapping.md`
