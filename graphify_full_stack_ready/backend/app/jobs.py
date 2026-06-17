from __future__ import annotations

import json
import threading
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .audit import audit
from .builder import build_graph_from_source
from .config import settings
from .models import BuildRequest


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class JobRecord:
    job_id: str
    status: str
    graph_id: str | None
    source_type: str | None
    message: str
    created_at: str
    updated_at: str
    error: str | None = None
    stats: dict[str, Any] | None = None


class JobStore:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._jobs: dict[str, JobRecord] = {}
        self._futures: dict[str, Future[Any]] = {}
        self._executor = ThreadPoolExecutor(max_workers=settings.job_workers)
        self._snapshot = settings.data_dir / "jobs.json"
        self._load()

    def _load(self) -> None:
        if not self._snapshot.exists():
            return
        try:
            data = json.loads(self._snapshot.read_text(encoding="utf-8"))
            with self._lock:
                for item in data:
                    if item.get("status") in {"running", "queued"}:
                        item["status"] = "failed"
                        item["error"] = "service_restarted_before_job_finished"
                    self._jobs[item["job_id"]] = JobRecord(**item)
        except Exception:
            return

    def _persist(self) -> None:
        with self._lock:
            data = [asdict(v) for v in self._jobs.values()]
        self._snapshot.parent.mkdir(parents=True, exist_ok=True)
        self._snapshot.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def create(self, request: BuildRequest) -> JobRecord:
        job_id = uuid.uuid4().hex[:16]
        record = JobRecord(
            job_id=job_id,
            status="queued",
            graph_id=request.options.graph_id,
            source_type=request.source.type,
            message="queued",
            created_at=now(),
            updated_at=now(),
        )
        with self._lock:
            self._jobs[job_id] = record
        self._persist()
        audit("job.created", job_id=job_id, source_type=request.source.type)
        return record

    def run_sync(self, job_id: str, request: BuildRequest) -> JobRecord:
        return self._run(job_id, request)

    def run_async(self, job_id: str, request: BuildRequest) -> None:
        future = self._executor.submit(self._run, job_id, request)
        with self._lock:
            self._futures[job_id] = future

    def _run(self, job_id: str, request: BuildRequest) -> JobRecord:
        self.update(job_id, status="running", message="running")
        try:
            graph = build_graph_from_source(job_id, request)
            record = self.update(job_id, status="succeeded", graph_id=graph["graph_id"], message="completed", stats=graph.get("stats"))
            return record
        except Exception as exc:
            audit("job.failed", job_id=job_id, error=str(exc))
            return self.update(job_id, status="failed", message="failed", error=str(exc))

    def update(self, job_id: str, **patch: Any) -> JobRecord:
        with self._lock:
            if job_id not in self._jobs:
                raise KeyError(job_id)
            rec = self._jobs[job_id]
            for k, v in patch.items():
                if hasattr(rec, k):
                    setattr(rec, k, v)
            rec.updated_at = now()
            out = rec
        self._persist()
        return out

    def get(self, job_id: str) -> JobRecord | None:
        with self._lock:
            return self._jobs.get(job_id)

    def cancel(self, job_id: str) -> JobRecord:
        with self._lock:
            rec = self._jobs.get(job_id)
            if not rec:
                raise KeyError(job_id)
            fut = self._futures.get(job_id)
            if fut and not fut.done():
                fut.cancel()
            rec.status = "cancelled"
            rec.message = "cancel requested"
            rec.updated_at = now()
        self._persist()
        audit("job.cancelled", job_id=job_id)
        return rec


job_store = JobStore()
