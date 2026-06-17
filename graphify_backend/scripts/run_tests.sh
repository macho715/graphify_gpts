#!/usr/bin/env bash
# End-to-end smoke test for the Graphify GPTS Backend.
#
# Boots uvicorn in the background, runs the OpenAPI acceptance test sequence
# from docs/04_BACKEND_IMPLEMENTATION_PLAN.md, then shuts the server down.
set -euo pipefail
cd "$(dirname "$0")/.."

export GRAPHIFY_API_KEYS="${GRAPHIFY_API_KEYS:-dev-smoke-key}"
export GRAPHIFY_URL_SECRET="${GRAPHIFY_URL_SECRET:-dev-smoke-secret-must-be-at-least-32-chars}"
export GRAPHIFY_WORK_ROOT="${GRAPHIFY_WORK_ROOT:-./var/smoke/workspaces}"
export GRAPHIFY_ARTIFACT_ROOT="${GRAPHIFY_ARTIFACT_ROOT:-./var/smoke/artifacts}"
export GRAPHIFY_AUDIT_LOG="${GRAPHIFY_AUDIT_LOG:-./var/smoke/audit.log}"
export GRAPHIFY_MAX_BUILD_SECONDS="${GRAPHIFY_MAX_BUILD_SECONDS:-300}"

# Pick a free port.
PORT="${PORT:-8765}"

echo "[smoke] starting uvicorn on :$PORT"
python -m uvicorn app.main:app --host 127.0.0.1 --port "$PORT" --log-level warning &
PID=$!
trap "kill $PID 2>/dev/null || true" EXIT

# Wait for /health.
for i in {1..40}; do
  if curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$PORT/health" | grep -q 200; then
    break
  fi
  sleep 0.5
done

python scripts/smoke_test.py --base "http://127.0.0.1:$PORT" --key "$GRAPHIFY_API_KEYS"
