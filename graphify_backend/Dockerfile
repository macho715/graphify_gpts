# Graphify GPTS Backend — Fly.io image
# Multi-stage: build deps in a slimmer runtime image.

FROM python:3.12-slim AS runtime

# graphify CLI is published on PyPI; install alongside the backend deps.
RUN apt-get update && apt-get install -y --no-install-recommends \
        git ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Install the graphify CLI on PATH so the runner can find it.
RUN pip install --no-cache-dir graphify

COPY app /app/app

# Fly mounts a writable volume at /data; persist workspaces + artifacts there
# so rebuilds and scale-out instances keep the same job state.
ENV GRAPHIFY_WORK_ROOT=/data/workspaces \
    GRAPHIFY_ARTIFACT_ROOT=/data/artifacts \
    GRAPHIFY_AUDIT_LOG=/data/audit.log \
    PYTHONIOENCODING=utf-8 \
    PYTHONUTF8=1 \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    LOG_LEVEL=INFO

EXPOSE 8000

# Single uvicorn worker — the in-process thread pool already parallelises jobs.
# Use a process supervisor (fly shuts the container down on signal).
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
