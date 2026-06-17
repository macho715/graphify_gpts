"""The actual build workflow, invoked from the background job thread.

Kept in its own module so the route handler stays small.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Callable

from . import audit
from .artifacts import materialize_build_artifacts
from .config import get_settings
from .fetcher import FetchError, fetch
from .graphify_runner import RunnerError, build, stats, update
from .jobs import attach_graph_id, load_workspace_for, patch_message
from .workspace import Workspace, workspace_size

_log = logging.getLogger("graphify.build")


def _check_workspace(ws: Workspace) -> None:
    settings = get_settings()
    size = workspace_size(ws)
    if size > settings.graphify_max_bytes:
        raise RunnerError(
            f"workspace size {size} exceeds cap {settings.graphify_max_bytes}"
        )


def run_build(
    job_id: str,
    *,
    input_uri: str,
    branch: str | None,
    mode: str,
    no_viz: bool,
    progress: Callable[[str], None] | None = None,
) -> tuple[str, str | None, str]:
    """Run a full build for `job_id` and return (status, graph_id, message)."""
    ws = load_workspace_for(job_id)
    progress = progress or (lambda m: patch_message(job_id, m))

    # 1. Fetch the corpus.
    progress("fetching corpus")
    try:
        fetch_result = fetch(ws, input_uri, branch=branch)
    except FetchError as exc:
        audit.audit("build.fetch_failed", job_id=job_id, error=str(exc))
        return ("failed", None, f"fetch: {exc}")

    audit.audit(
        "build.fetched",
        job_id=job_id,
        kind=fetch_result.input_kind,
        bytes=fetch_result.bytes_pulled,
        skipped=fetch_result.skipped_files,
    )
    progress(
        f"fetched {fetch_result.input_kind} "
        f"({fetch_result.bytes_pulled:,} bytes, "
        f"{fetch_result.skipped_files} sensitive files skipped)"
    )

    # 2. Build the graph.
    progress("extracting graph")
    res = build(ws, no_viz=no_viz, force=True)
    if res.returncode != 0:
        err = (res.stderr or res.stdout or "").strip()[:500]
        audit.audit("build.extract_failed", job_id=job_id, stderr=err)
        return ("failed", None, f"graphify update failed: {err}")

    # 3. Compute stats (must happen before materializing artifacts).
    try:
        s = stats(ws)
    except RunnerError as exc:
        return ("failed", None, f"stats: {exc}")

    # 4. Materialize artifacts.
    progress("materializing artifacts")
    materialize_build_artifacts(ws)
    attach_graph_id(job_id, job_id)

    audit.audit(
        "build.succeeded",
        job_id=job_id,
        nodes=s["nodes"],
        edges=s["edges"],
        communities=s["communities"],
        mode=mode,
    )
    return (
        "succeeded",
        job_id,
        (
            f"graph built: {s['nodes']} nodes, {s['edges']} edges, "
            f"{s['communities']} communities; "
            f"EXTRACTED {s['extracted_pct']}%, INFERRED {s['inferred_pct']}%, "
            f"AMBIGUOUS {s['ambiguous_pct']}%"
        ),
    )


def run_update(job_id: str) -> tuple[str, str | None, str]:
    """Incremental update against an existing graph."""
    ws = load_workspace_for(job_id)
    progress = lambda m: patch_message(job_id, m)  # noqa: E731
    progress("updating graph incrementally")
    res = update(ws)
    if res.returncode != 0:
        err = (res.stderr or res.stdout or "").strip()[:500]
        audit.audit("update.failed", job_id=job_id, stderr=err)
        return ("failed", None, f"graphify update failed: {err}")
    materialize_build_artifacts(ws)
    s = stats(ws)
    audit.audit("update.succeeded", job_id=job_id, nodes=s["nodes"], edges=s["edges"])
    return (
        "succeeded",
        job_id,
        f"graph updated: {s['nodes']} nodes, {s['edges']} edges",
    )
