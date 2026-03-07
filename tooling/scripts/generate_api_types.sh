#!/usr/bin/env bash
set -euo pipefail
python packages/types/scripts/generate_api_contract.py
python packages/types/scripts/generate_api_types.py
python packages/types/check_types.py
