#!/usr/bin/env bash
set -euo pipefail
python -m compileall apps packages >/dev/null
echo "lint_repo: compile check ok"
