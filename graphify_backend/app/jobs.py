"""In-memory job store with thread-safe updates and JSONL persistence.

The job manager owns the lifecycle of a build/update job:
  queued → running → (succeeded | failed | cancelled)

A single-thread executor runs jobs in the background; the request thread
returns immediately with a Job envelope so the GPT Action client can poll.
"""

from __future__ import annotations

import json
import logging
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from . import audit
from .config import get_settings
from .models import Job

_log = logging.getLogger("graphify.jobs")

_lock = threading.RLock()
_jobs: dict[str, Job] = {}
_futures: dict[str, Future] = {}
_pool: ThreadPoolExecutor | None = None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _persist() -> None:
    """Snapshot the job map to disk for crash recovery."""
    settings = get_settings()
    snapshot = settings.graphify_work_root / "_jobs.jsonl"
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        lines = [j.model_dump_json() for j in _jobs.values()]
    snapshot.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _restore() -> None:
    """Reload job snapshots written by previous runs."""
    global _jobs
    settings = get_settings()
    snapshot = settings.graphify_work_root / "_jobs.jsonl"
    if not snapshot.exists():
        return
    for line in snapshot.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            j = Job.model_validate_json(line)
        except Exception:  # noqa: BLE001
            continue
        # Anything that was running or queued is now effectively dead.
        if j.status in {"queued", "running"}:
            j = j.model_copy(update={"status": "failed", "message": "server restarted"})
        _jobs[j.job_id] = j


def get_pool() -> ThreadPoolExecutor:
    global _pool
    if _pool is None:
        _pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="graphify-job")
    return _pool


def restore_once() -> None:
    _restore()


# ---------- Public API ----------


def get(job_id: str) -> Job | None:
    with _lock:
        return _jobs.get(job_id)


def list_all() -> list[Job]:
    with _lock:
        return sorted(_jobs.values(), key=lambda j: j.created_at, reverse=True)


def submit(
    *,
    initial: Job,
    work_fn: Callable[[], tuple[str, str | None, str]],
) -> Job:
    """Submit a background job. `work_fn` returns (status, graph_id, message)."""
    with _lock:
        _jobs[initial.job_id] = initial
        _persist()
    fut = get_pool().submit(_runner, initial.job_id, work_fn)
    with _lock:
        _futures[initial.job_id] = fut
    audit.audit("job.submitted", job_id=initial.job_id, status=initial.status)
    return initial


def cancel(job_id: str) -> Job | None:
    with _lock:
        fut = _futures.get(job_id)
        job = _jobs.get(job_id)
        if job is None:
            return None
        if fut is not None and not fut.done():
            fut.cancel()
        updated = job.model_copy(
            update={"status": "cancelled", "updated_at": _now(), "message": "cancelled by user"}
        )
        _jobs[job_id] = updated
        _persist()
    audit.audit("job.cancelled", job_id=job_id)
    return updated


# ---------- Internals ----------


def _runner(job_id: str, work_fn: Callable[[], tuple[str, str | None, str]]) -> None:
    with _lock:
        current = _jobs.get(job_id)
        if current is None:
            return
        running = current.model_copy(update={"status": "running", "updated_at": _now()})
        _jobs[job_id] = running
    audit.audit("job.running", job_id=job_id)
    try:
        status, graph_id, message = work_fn()
        with _lock:
            current = _jobs.get(job_id)
            if current is None:
                return
            updated = current.model_copy(
                update={
                    "status": status,
                    "graph_id": graph_id or current.graph_id,
                    "message": message,
                    "updated_at": _now(),
                }
            )
            _jobs[job_id] = updated
        _persist()
        audit.audit("job.done", job_id=job_id, status=status, graph_id=graph_id)
    except Exception as exc:  # noqa: BLE001
        _log.exception("job %s failed", job_id)
        with _lock:
            current = _jobs.get(job_id)
            if current is not None:
                failed = current.model_copy(
                    update={
                        "status": "failed",
                        "message": f"{type(exc).__name__}: {exc}",
                        "updated_at": _now(),
                    }
                )
                _jobs[job_id] = failed
        _persist()
        audit.audit("job.failed", job_id=job_id, error=str(exc))
    finally:
        with _lock:
            _futures.pop(job_id, None)


def attach_graph_id(job_id: str, graph_id: str) -> None:
    """Helper for the build flow: stamp the graph_id when the build succeeds."""
    with _lock:
        current = _jobs.get(job_id)
        if current is None:
            return
        _jobs[job_id] = current.model_copy(
            update={"graph_id": graph_id, "updated_at": _now()}
        )
    _persist()


def patch_message(job_id: str, message: str) -> None:
    with _lock:
        current = _jobs.get(job_id)
        if current is None:
            return
        _jobs[job_id] = current.model_copy(
            update={"message": message, "updated_at": _now()}
        )


def new_job_id() -> str:
    """Helper: allocate a job_id derived from a fresh workspace."""
    from .workspace import create_workspace

    ws = create_workspace()
    return ws.job_id


def load_workspace_for(job_id: str):
    """Resolve a job_id back to its workspace paths."""
    from .workspace import Workspace

    s = get_settings()
    return Workspace(
        job_id=job_id,
        work_dir=s.graphify_work_root / job_id,
        artifact_dir=s.graphify_artifact_root / job_id,
        created_at=datetime.now(timezone.utc),
    )


def delete_job(job_id: str) -> bool:
    """Hard-delete a job, its workspace and its artifacts. Admin only."""
    from .workspace import destroy_workspace

    with _lock:
        job = _jobs.pop(job_id, None)
        fut = _futures.pop(job_id, None)
    if fut is not None and not fut.done():
        fut.cancel()
    ws = load_workspace_for(job_id)
    destroy_workspace(ws)
    _persist()
    if job is None:
        return False
    audit.audit("job.deleted", job_id=job_id)
    return True
