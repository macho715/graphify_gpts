from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl

SourceType = Literal["git", "zip_url", "inline_files", "local_path"]
JobStatus = Literal["queued", "running", "succeeded", "failed", "cancelled"]
ExportFormat = Literal["json", "report", "html", "zip"]


class InlineFile(BaseModel):
    path: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., max_length=1_000_000)


class GraphifySource(BaseModel):
    type: SourceType
    url: str | None = None
    branch: str | None = None
    files: list[InlineFile] | None = None
    path: str | None = None


class BuildOptions(BaseModel):
    graph_id: str | None = None
    include_patterns: list[str] = Field(default_factory=list)
    exclude_patterns: list[str] = Field(default_factory=list)
    max_files: int | None = Field(default=None, ge=1, le=100_000)
    synchronous: bool = True
    audit_label: str | None = None


class BuildRequest(BaseModel):
    source: GraphifySource
    options: BuildOptions = Field(default_factory=BuildOptions)


class BuildResponse(BaseModel):
    job_id: str
    status: JobStatus
    graph_id: str | None = None
    message: str


class JobInfo(BaseModel):
    job_id: str
    status: JobStatus
    graph_id: str | None = None
    source_type: str | None = None
    message: str = ""
    created_at: str
    updated_at: str
    error: str | None = None
    stats: dict[str, Any] | None = None


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(default=10, ge=1, le=50)
    node_types: list[str] = Field(default_factory=list)


class QueryHit(BaseModel):
    node_id: str
    label: str
    type: str
    score: float
    evidence: str | None = None
    path: str | None = None


class QueryResponse(BaseModel):
    graph_id: str
    query: str
    hits: list[QueryHit]


class PathRequest(BaseModel):
    source: str = Field(..., min_length=1, max_length=500)
    target: str = Field(..., min_length=1, max_length=500)
    max_depth: int = Field(default=6, ge=1, le=20)


class PathResponse(BaseModel):
    graph_id: str
    found: bool
    path: list[dict[str, Any]] = Field(default_factory=list)
    edges: list[dict[str, Any]] = Field(default_factory=list)


class ExplainRequest(BaseModel):
    node_id: str | None = None
    query: str | None = None
    depth: int = Field(default=1, ge=0, le=3)


class ExplainResponse(BaseModel):
    graph_id: str
    node: dict[str, Any] | None
    neighbors: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    summary: str


class AffectedRequest(BaseModel):
    node_id: str | None = None
    query: str | None = None
    direction: Literal["out", "in", "both"] = "both"
    max_depth: int = Field(default=2, ge=1, le=6)
    limit: int = Field(default=50, ge=1, le=200)


class AffectedResponse(BaseModel):
    graph_id: str
    start_node: dict[str, Any] | None
    affected: list[dict[str, Any]]
    edges: list[dict[str, Any]]


class UpdateRequest(BaseModel):
    source: GraphifySource | None = None
    options: BuildOptions = Field(default_factory=BuildOptions)


class ExportRequest(BaseModel):
    format: ExportFormat


class ExportResponse(BaseModel):
    graph_id: str
    format: ExportFormat
    artifact_token: str
    artifact_url: str
    expires_in_seconds: int


class StatsResponse(BaseModel):
    graph_id: str
    nodes: int
    edges: int
    files: int
    symbols: int
    skipped_files: int
    generated_at: str
    source: dict[str, Any]
