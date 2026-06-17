"""Graph operations: update / stats / query / path / explain / affected / export / download."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse

from .. import audit
from ..artifacts import (
    FORMAT_MAP,
    artifact_path,
    issue_signed_url,
    materialize_build_artifacts,
    resolve_signed_url,
)
from ..auth import require_bearer
from ..build_pipeline import run_update
from ..config import get_settings
from ..graphify_runner import RunnerError, stats
from ..jobs import Job, get, load_workspace_for, new_job_id, submit
from ..models import (
    AffectedRequest,
    ExportRequest,
    ExportResponse,
    ExplainRequest,
    GraphStats,
    PathRequest,
    QueryRequest,
    TextResult,
)
from ..query_service import run_affected, run_explain, run_path, run_query

router = APIRouter(prefix="/v1/graphify/graphs", tags=["graphs"])
_log = logging.getLogger("graphify.routes.graphs")

_SLUG_RE = re.compile(r"[^A-Za-z0-9_.-]+")


def _load_workspace_or_404(graph_id: str):
    ws = load_workspace_for(graph_id)
    if not (ws.artifact_dir / "graph.json").exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"graph '{graph_id}' not found",
        )
    return ws


def _initial_job(job_id: str) -> Job:
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    return Job(
        job_id=job_id,
        status="queued",
        graph_id=job_id,
        message="queued",
        created_at=now,
        updated_at=now,
    )


# ---------- Update ----------


@router.post(
    "/{graph_id}/update",
    response_model=Job,
    operation_id="graphifyUpdate",
    summary="Incrementally update an existing graph.",
)
async def update_graph(graph_id: str, _key: str = Depends(require_bearer)) -> Job:
    _load_workspace_or_404(graph_id)
    job = _initial_job(graph_id)
    submit(initial=job, work_fn=lambda: run_update(graph_id))
    return job


# ---------- Stats ----------


@router.get(
    "/{graph_id}/stats",
    response_model=GraphStats,
    operation_id="graphifyStats",
    summary="Get graph statistics and top nodes.",
)
async def graph_stats(graph_id: str, _key: str = Depends(require_bearer)) -> GraphStats:
    ws = _load_workspace_or_404(graph_id)
    try:
        s = stats(ws)
    except RunnerError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc
    return GraphStats(**s)


# ---------- Query / Path / Explain / Affected ----------


@router.post(
    "/{graph_id}/query",
    response_model=TextResult,
    operation_id="graphifyQuery",
    summary="Query an existing graph using BFS or DFS traversal.",
)
async def graph_query(
    graph_id: str, body: QueryRequest, _key: str = Depends(require_bearer)
) -> TextResult:
    ws = _load_workspace_or_404(graph_id)
    audit.audit(
        "graph.query",
        graph_id=graph_id,
        question=body.question,
        mode=body.mode,
        budget=body.token_budget,
    )
    return run_query(
        ws,
        question=body.question,
        mode=body.mode,
        token_budget=body.token_budget,
        context_filter=body.context_filter,
    )


@router.post(
    "/{graph_id}/path",
    response_model=TextResult,
    operation_id="graphifyPath",
    summary="Find shortest path between two concepts.",
)
async def graph_path(
    graph_id: str, body: PathRequest, _key: str = Depends(require_bearer)
) -> TextResult:
    ws = _load_workspace_or_404(graph_id)
    return run_path(ws, source=body.source, target=body.target, max_hops=body.max_hops)


@router.post(
    "/{graph_id}/explain",
    response_model=TextResult,
    operation_id="graphifyExplain",
    summary="Explain a node and its neighborhood.",
)
async def graph_explain(
    graph_id: str, body: ExplainRequest, _key: str = Depends(require_bearer)
) -> TextResult:
    ws = _load_workspace_or_404(graph_id)
    return run_explain(ws, label=body.label, depth=body.depth)


@router.post(
    "/{graph_id}/affected",
    response_model=TextResult,
    operation_id="graphifyAffected",
    summary="Find reverse traversal impact/blast radius.",
)
async def graph_affected(
    graph_id: str, body: AffectedRequest, _key: str = Depends(require_bearer)
) -> TextResult:
    ws = _load_workspace_or_404(graph_id)
    return run_affected(
        ws, label=body.label, relations=body.relation, depth=body.depth
    )


# ---------- Export ----------


@router.post(
    "/{graph_id}/export",
    response_model=ExportResponse,
    operation_id="graphifyExport",
    summary="Export a graph artifact.",
)
async def graph_export(
    graph_id: str,
    body: ExportRequest,
    request: Request,
    _key: str = Depends(require_bearer),
) -> ExportResponse:
    ws = _load_workspace_or_404(graph_id)
    if body.format not in FORMAT_MAP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"unsupported format: {body.format}",
        )
    try:
        path = artifact_path(ws, body.format)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc

    relative, expires_at = issue_signed_url(ws, body.format, str(request.base_url))
    full_url = str(request.base_url).rstrip("/") + relative
    audit.audit(
        "graph.export",
        graph_id=graph_id,
        format=body.format,
        bytes=path.stat().st_size if path.exists() else 0,
    )
    return ExportResponse(
        graph_id=graph_id,
        format=body.format,
        download_url=full_url,
        expires_at=expires_at,
    )


# ---------- Signed artifact download ----------


artifacts_router = APIRouter(prefix="/v1/graphify", tags=["artifacts"])


@artifacts_router.get(
    "/artifacts/{token}",
    operation_id="graphifyArtifactDownload",
    summary="Download a previously exported artifact via a signed token.",
    description=(
        "Public endpoint — the OpenAPI schema marks this with `security: []`. "
        "The token is HMAC-signed and self-expiring, so Bearer auth is not required."
    ),
)
async def download_artifact(token: str) -> FileResponse:
    try:
        path, mime, filename = resolve_signed_url(token)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_410_GONE, detail=str(exc)
        ) from exc
    audit.audit("graph.artifact.download", filename=filename)
    return FileResponse(
        path=str(path),
        media_type=mime,
        filename=filename,
        headers={"Cache-Control": "no-store"},
    )
