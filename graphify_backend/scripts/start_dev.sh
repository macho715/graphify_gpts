#!/usr/bin/env bash
# Graphify GPTS Backend — dev launcher.
# Reads .env, runs uvicorn with hot reload.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
