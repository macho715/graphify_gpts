FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    GRAPHIFY_DATA_DIR=/data \
    GRAPHIFY_WORK_DIR=/data/workspaces \
    GRAPHIFY_GRAPH_DIR=/data/graphs \
    GRAPHIFY_ARTIFACT_DIR=/data/artifacts \
    GRAPHIFY_AUDIT_LOG=/data/audit.jsonl

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
# Build context is the repo root (Railway monorepo). Reference files via
# their repo-relative path; the active backend ships at this fixed location.
COPY graphify_full_stack_ready/backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY graphify_full_stack_ready/backend/app /app/app
RUN mkdir -p /data/workspaces /data/graphs /data/artifacts
EXPOSE 8000
# Railway injects $PORT; default to 8000 for local parity.
# Generous start-period to absorb cold-start imports on Railway.
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 CMD curl -fsS http://127.0.0.1:${PORT:-8000}/health || exit 1
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
