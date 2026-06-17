#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export GRAPHIFY_ALLOW_LOCAL_PATH=${GRAPHIFY_ALLOW_LOCAL_PATH:-true}
export GRAPHIFY_AUTH_MODE=${GRAPHIFY_AUTH_MODE:-none}
export GRAPHIFY_DATA_DIR=${GRAPHIFY_DATA_DIR:-./data}
python -m uvicorn app.main:app --host 127.0.0.1 --port "${PORT:-8000}" --reload
