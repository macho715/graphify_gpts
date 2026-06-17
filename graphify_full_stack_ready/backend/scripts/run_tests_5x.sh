#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export GRAPHIFY_ALLOW_LOCAL_PATH=true
export GRAPHIFY_AUTH_MODE=none
export GRAPHIFY_DATA_DIR="${GRAPHIFY_DATA_DIR:-./data_test}"
export GRAPHIFY_WORK_DIR="$GRAPHIFY_DATA_DIR/workspaces"
export GRAPHIFY_GRAPH_DIR="$GRAPHIFY_DATA_DIR/graphs"
export GRAPHIFY_ARTIFACT_DIR="$GRAPHIFY_DATA_DIR/artifacts"
export GRAPHIFY_AUDIT_LOG="$GRAPHIFY_DATA_DIR/audit.jsonl"
PORT="${PORT:-8765}"
python -m uvicorn app.main:app --host 127.0.0.1 --port "$PORT" > /tmp/graphify_backend_test.log 2>&1 &
PID=$!
cleanup() { kill "$PID" >/dev/null 2>&1 || true; }
trap cleanup EXIT
for i in $(seq 1 60); do
  if python - <<PY >/dev/null 2>&1
import httpx
r=httpx.get('http://127.0.0.1:$PORT/health', timeout=1)
raise SystemExit(0 if r.status_code==200 else 1)
PY
  then
    break
  fi
  sleep 0.25
done
TMP_DIR="$(mktemp -d)"
for round in 1 2 3 4 5; do
  echo "=== acceptance round $round/5 ==="
  python scripts/smoke_test_5x.py \
    --base-url "http://127.0.0.1:$PORT" \
    --graph-id "smoke-tiny-r${round}" \
    --report "$TMP_DIR/round_${round}.md"
done
python - <<PY
from pathlib import Path
import re
root=Path('$TMP_DIR')
out=Path('../TEST_REPORT.md')
sections=[]
pass_count=0
fail_count=0
for i in range(1,6):
    text=(root/f'round_{i}.md').read_text(encoding='utf-8')
    sections.append(f'## Round {i}\n\n'+text)
    pass_count += text.count('| PASS |')
    fail_count += text.count('| FAIL |')
summary=[
    '# Graphify Backend Acceptance Test Report — 5 Rounds',
    '',
    f'- Rounds: 5',
    f'- Checks per round: 7',
    f'- Total checks: 35',
    f'- PASS checks: {pass_count}',
    f'- FAIL checks: {fail_count}',
    f'- Result: {"PASS" if fail_count==0 and pass_count>=35 else "FAIL"}',
    '',
]
out.write_text('\n'.join(summary+sections), encoding='utf-8')
print(f'WROTE {out} PASS={pass_count} FAIL={fail_count}')
PY
