#!/usr/bin/env bash
set -euo pipefail

python apps/backend/manage.py migrate --noinput
python apps/backend/manage.py runserver 127.0.0.1:8000
