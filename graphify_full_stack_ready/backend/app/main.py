from __future__ import annotations

import shutil
from dataclasses import asdict
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse

from .artifacts import sign_artifact, verify_artifact
from .auth import require_auth
from .builder import create_export, graph_path, load_graph
from .config import settings
from .graph_ops import affected_nodes, explain_node, find_nodes, shortest_path
from .jobs import job_store
from .models import (
    AffectedRequest,
    AffectedResponse,
    BuildRequest,
    BuildResponse,
    ExplainRequest,
    ExplainResponse,
    ExportRequest,
    ExportResponse,
    JobInfo,
    PathRequest,
    PathResponse,
    QueryRequest,
    QueryResponse,
    StatsResponse,
    UpdateRequest,
)

app = FastAPI(title="Graphify GPTS Backend", version="1.0.0", description="Graphify-style persistent knowledge graph backend for Custom GPT Actions.")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": str(exc), "type": exc.__class__.__name__})


@app.get("/")
def root():
    return {"service": settings.service_name, "status": "ok", "docs": "/docs"}


@app.get("/health", operation_id="graphifyHealth")
def health():
    return {
        "status": "ok",
        "auth_mode": settings.auth_mode,
        "data_dir": str(settings.data_dir),
        "allowed_hosts": list(settings.allowed_hosts),
        "run_mode": settings.run_mode,
    }


@app.post("/v1/graphify/jobs", response_model=BuildResponse, operation_id="graphifyBuild", dependencies=[Depends(require_auth)])
def graphify_build(request: BuildRequest):
    record = job_store.create(request)
    if request.options.synchronous:
        record = job_store.run_sync(record.job_id, request)
    else:
        job_store.run_async(record.job_id, request)
    return BuildResponse(job_id=record.job_id, status=record.status, graph_id=record.graph_id, message=record.message)


@app.get("/v1/graphify/jobs/{job_id}", response_model=JobInfo, operation_id="graphifyJobStatus", dependencies=[Depends(require_auth)])
def graphify_job_status(job_id: str):
    record = job_store.get(job_id)
    if not record:
        raise HTTPException(status_code=404, detail="job not found")
    return JobInfo(**asdict(record))


@app.delete("/v1/graphify/jobs/{job_id}", response_model=JobInfo, operation_id="graphifyJobCancel", dependencies=[Depends(require_auth)])
def graphify_job_cancel(job_id: str):
    try:
        record = job_store.cancel(job_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="job not found")
    return JobInfo(**asdict(record))


@app.post("/v1/graphify/graphs/{graph_id}/update", response_model=BuildResponse, operation_id="graphifyUpdate", dependencies=[Depends(require_auth)])
def graphify_update(graph_id: str, request: UpdateRequest):
    graph = _load_or_404(graph_id)
    source_data = request.source or graph.get("source")
    if not source_data:
        raise HTTPException(status_code=400, detail="No prior source is available for update")
    if not hasattr(source_data, "model_dump"):
        # Rehydrate pydantic models lazily to avoid circular imports in schema objects.
        from .models import GraphifySource

        source_data = GraphifySource(**source_data)
    request.options.graph_id = graph_id
    build_request = BuildRequest(source=source_data, options=request.options)
    record = job_store.create(build_request)
    if build_request.options.synchronous:
        record = job_store.run_sync(record.job_id, build_request)
    else:
        job_store.run_async(record.job_id, build_request)
    return BuildResponse(job_id=record.job_id, status=record.status, graph_id=record.graph_id, message=record.message)


@app.get("/v1/graphify/graphs/{graph_id}/stats", response_model=StatsResponse, operation_id="graphifyStats", dependencies=[Depends(require_auth)])
def graphify_stats(graph_id: str):
    graph = _load_or_404(graph_id)
    stats = graph.get("stats", {})
    return StatsResponse(
        graph_id=graph_id,
        nodes=stats.get("nodes", 0),
        edges=stats.get("edges", 0),
        files=stats.get("files", 0),
        symbols=stats.get("symbols", 0),
        skipped_files=stats.get("skipped_files", 0),
        generated_at=graph.get("generated_at", ""),
        source=graph.get("source", {}),
    )


@app.post("/v1/graphify/graphs/{graph_id}/query", response_model=QueryResponse, operation_id="graphifyQuery", dependencies=[Depends(require_auth)])
def graphify_query(graph_id: str, request: QueryRequest):
    graph = _load_or_404(graph_id)
    return QueryResponse(graph_id=graph_id, query=request.query, hits=find_nodes(graph, request.query, request.limit, request.node_types))


@app.post("/v1/graphify/graphs/{graph_id}/path", response_model=PathResponse, operation_id="graphifyPath", dependencies=[Depends(require_auth)])
def graphify_path(graph_id: str, request: PathRequest):
    graph = _load_or_404(graph_id)
    nodes, edges = shortest_path(graph, request.source, request.target, request.max_depth)
    return PathResponse(graph_id=graph_id, found=bool(nodes), path=nodes, edges=edges)


@app.post("/v1/graphify/graphs/{graph_id}/explain", response_model=ExplainResponse, operation_id="graphifyExplain", dependencies=[Depends(require_auth)])
def graphify_explain(graph_id: str, request: ExplainRequest):
    graph = _load_or_404(graph_id)
    data = explain_node(graph, request.node_id, request.query, request.depth)
    return ExplainResponse(graph_id=graph_id, **data)


@app.post("/v1/graphify/graphs/{graph_id}/affected", response_model=AffectedResponse, operation_id="graphifyAffected", dependencies=[Depends(require_auth)])
def graphify_affected(graph_id: str, request: AffectedRequest):
    graph = _load_or_404(graph_id)
    data = affected_nodes(graph, request.node_id, request.query, request.direction, request.max_depth, request.limit)
    return AffectedResponse(graph_id=graph_id, **data)


@app.post("/v1/graphify/graphs/{graph_id}/export", response_model=ExportResponse, operation_id="graphifyExport", dependencies=[Depends(require_auth)])
def graphify_export(graph_id: str, request: ExportRequest, http_request: Request):
    _load_or_404(graph_id)
    file_path = create_export(graph_id, request.format)
    token = sign_artifact(graph_id, request.format, file_path)
    base = settings.public_base_url or str(http_request.base_url).rstrip("/")
    return ExportResponse(
        graph_id=graph_id,
        format=request.format,
        artifact_token=token,
        artifact_url=f"{base}/v1/graphify/artifacts/{token}",
        expires_in_seconds=settings.url_ttl_seconds,
    )


@app.get("/v1/graphify/artifacts/{token}", operation_id="graphifyArtifactDownload")
def graphify_artifact_download(token: str):
    payload = verify_artifact(token)
    path = Path(payload["path"])
    media = {
        "json": "application/json",
        "report": "text/markdown; charset=utf-8",
        "html": "text/html; charset=utf-8",
        "zip": "application/zip",
    }.get(payload.get("format"), "application/octet-stream")
    return FileResponse(path, media_type=media, filename=path.name)


def _load_or_404(graph_id: str):
    try:
        return load_graph(graph_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="graph not found")
