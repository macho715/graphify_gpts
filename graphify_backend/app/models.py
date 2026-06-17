"""Pydantic schemas mirroring 03_OPENAPI_ACTION_SCHEMA.yaml.

These are the wire contracts. Any change here MUST match the OpenAPI schema
that the Custom GPT Action consumes.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# ---------- Shared ----------


class _StrictModel(BaseModel):
    """Base model that mirrors `additionalProperties: false` in the OpenAPI
    schema. Pydantic v2's `extra="forbid"` is the strict equivalent.
    """

    model_config = ConfigDict(extra="forbid")


class ErrorResponse(_StrictModel):
    detail: str


# ---------- Job ----------


class Job(_StrictModel):
    job_id: str
    status: Literal["queued", "running", "succeeded", "failed", "cancelled"]
    graph_id: str | None = None
    message: str = ""
    created_at: datetime
    updated_at: datetime


# ---------- Build / Update ----------


class BuildRequest(_StrictModel):
    input_uri: str = Field(
        ..., description="Public GitHub/repo/archive/document URI accessible by the backend."
    )
    branch: str | None = None
    mode: Literal["standard", "deep"] = "standard"
    directed: bool = True
    no_viz: bool = False
    options: dict[str, Any] = Field(default_factory=dict)


class UpdateRequest(_StrictModel):
    """Empty body — incremental update is path-scoped by graph_id."""

    options: dict[str, Any] = Field(default_factory=dict)


# ---------- Query / Path / Explain / Affected / Export ----------


class QueryRequest(_StrictModel):
    question: str
    mode: Literal["bfs", "dfs"] = "bfs"
    token_budget: int = Field(default=2000, ge=200, le=12000)
    context_filter: list[str] = Field(default_factory=list)


class PathRequest(_StrictModel):
    source: str
    target: str
    max_hops: int = Field(default=8, ge=1, le=64)


class ExplainRequest(_StrictModel):
    label: str
    depth: int = Field(default=2, ge=1, le=6)


class AffectedRequest(_StrictModel):
    label: str
    relation: list[str] = Field(default_factory=list)
    depth: int = Field(default=2, ge=1, le=6)


class ExportRequest(_StrictModel):
    format: Literal["json", "html", "svg", "graphml", "wiki", "cypher", "callflow_html"]


# ---------- Responses ----------


class EvidenceItem(_StrictModel):
    node: str
    source_file: str
    source_location: str = ""
    confidence: str = "EXTRACTED"


class TopNode(_StrictModel):
    label: str
    degree: int
    source_file: str = ""


class GraphStats(_StrictModel):
    graph_id: str
    nodes: int
    edges: int
    communities: int
    extracted_pct: float
    inferred_pct: float
    ambiguous_pct: float
    top_nodes: list[TopNode] = Field(default_factory=list)


class TextResult(_StrictModel):
    graph_id: str
    result: str
    evidence: list[EvidenceItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ExportResponse(_StrictModel):
    graph_id: str
    format: str
    download_url: str
    expires_at: datetime
