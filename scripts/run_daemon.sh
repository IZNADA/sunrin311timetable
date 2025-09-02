#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

# Activate venv if present
if [ -d "venv" ]; then
  # shellcheck disable=SC1091
  source venv/bin/activate
fi

export PYTHONUNBUFFERED=1

RUN_NOW=false
if [[ "${1:-}" == "--run-now" ]]; then
  RUN_NOW=true
fi

if $RUN_NOW; then
  python -m src.daemon --run-now
else
  python -m src.daemon
fi

