"""Per-job workspace management.

A job owns:
  * `work_dir`     — temp dir where the corpus is fetched/extracted.
  * `artifact_dir` — versioned directory that holds graph.json, GRAPH_REPORT.md,
                     graph.html and any export artifacts.

Both live under the configured roots. Workspaces are torn down on cancellation
or after a configurable retention window.
"""

from __future__ import annotations

import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .config import get_settings


@dataclass(frozen=True)
class Workspace:
    job_id: str
    work_dir: Path
    artifact_dir: Path
    created_at: datetime


def _job_root(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    return root


def create_workspace() -> Workspace:
    """Create a fresh workspace for a new job."""
    s = get_settings()
    job_id = uuid.uuid4().hex[:12]
    work_dir = _job_root(s.graphify_work_root) / job_id
    artifact_dir = _job_root(s.graphify_artifact_root) / job_id
    work_dir.mkdir(parents=True, exist_ok=False)
    artifact_dir.mkdir(parents=True, exist_ok=False)
    return Workspace(
        job_id=job_id,
        work_dir=work_dir,
        artifact_dir=artifact_dir,
        created_at=datetime.now(timezone.utc),
    )


def destroy_workspace(ws: Workspace) -> None:
    """Best-effort cleanup. Errors are swallowed but logged via OSError."""
    for d in (ws.work_dir, ws.artifact_dir):
        try:
            if d.exists():
                shutil.rmtree(d)
        except OSError:
            pass


def workspace_size(ws: Workspace) -> int:
    """Total bytes consumed by the workspace (file content only)."""
    total = 0
    for root in (ws.work_dir, ws.artifact_dir):
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if p.is_file():
                try:
                    total += p.stat().st_size
                except OSError:
                    pass
    return total
