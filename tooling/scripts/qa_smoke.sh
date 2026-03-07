#!/usr/bin/env bash
set -euo pipefail

python apps/backend/manage.py migrate --noinput
python apps/backend/manage.py check
pytest -q server/tests/test_projects_api_exports.py
pytest -q server/tests/test_api.py -k 'health or frontend_bootstrap or auth_session_bridge_login_me_logout_api or research_note_files_api_returns_note_file_rows or project_research_files_api_returns_tokens_and_labels'
(
  cd apps/web
  npm ci
  npm run build
)
