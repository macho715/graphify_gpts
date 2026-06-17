"""Artifact storage and signed download URLs.

After a build the runner produces:
  * <artifact_dir>/graph.json
  * <artifact_dir>/GRAPH_REPORT.md
  * <artifact_dir>/graph.html  (unless --no-viz)

The /export endpoint materializes other formats on demand and exposes them via
HMAC-signed URLs that the `/artifacts/{token}` endpoint validates.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from .config import get_settings
from .workspace import Workspace

# Format → (filename inside artifact_dir, generator callable, MIME type)
FORMAT_MAP: dict[str, tuple[str, str]] = {
    "json": ("graph.json", "application/json"),
    "html": ("graph.html", "text/html; charset=utf-8"),
    "svg": ("graph.svg", "image/svg+xml"),
    "graphml": ("graph.graphml", "application/xml"),
    "wiki": ("wiki/index.md", "text/markdown; charset=utf-8"),
    "cypher": ("graph.cypher", "text/plain; charset=utf-8"),
    "callflow_html": ("callflow.html", "text/html; charset=utf-8"),
}


def _serializer() -> URLSafeTimedSerializer:
    s = get_settings()
    return URLSafeTimedSerializer(s.graphify_url_secret, salt="graphify-artifact")


def materialize_build_artifacts(ws: Workspace) -> None:
    """Copy graph.json / GRAPH_REPORT.md / graph.html from work to artifact dir."""
    src = ws.work_dir / "corpus" / "graphify-out"
    if not src.exists():
        return
    for fname in ("graph.json", "GRAPH_REPORT.md", "graph.html"):
        s = src / fname
        if s.exists():
            shutil.copy2(s, ws.artifact_dir / fname)


def artifact_path(ws: Workspace, fmt: str) -> Path:
    """Return the on-disk path for a given export format. Generates on demand."""
    if fmt not in FORMAT_MAP:
        raise KeyError(f"unsupported format: {fmt}")
    fname, _mime = FORMAT_MAP[fmt]
    target = ws.artifact_dir / fname
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        return target
    _generate_artifact(ws, fmt, target)
    return target


def _generate_artifact(ws: Workspace, fmt: str, target: Path) -> None:
    """Produce the requested artifact from the canonical graph.json."""
    graph = ws.artifact_dir / "graph.json"
    if not graph.exists():
        raise FileNotFoundError(f"graph.json missing for job {ws.job_id}")
    data = json.loads(graph.read_text(encoding="utf-8"))
    # Normalize: graphify emits `links`, other tools emit `edges`. Alias.
    if "edges" not in data and "links" in data:
        data["edges"] = data["links"]
    if fmt == "json":
        target.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    elif fmt == "html":
        # Re-use the built-in graph.html if it exists; otherwise emit a stub.
        bundled = ws.artifact_dir / "graph.html"
        if bundled.exists():
            shutil.copy2(bundled, target)
        else:
            target.write_text(_minimal_html(data), encoding="utf-8")
    elif fmt == "svg":
        target.write_text(_render_svg(data), encoding="utf-8")
    elif fmt == "graphml":
        target.write_text(_render_graphml(data), encoding="utf-8")
    elif fmt == "cypher":
        target.write_text(_render_cypher(data), encoding="utf-8")
    elif fmt == "wiki":
        target.write_text(_render_wiki(data), encoding="utf-8")
    elif fmt == "callflow_html":
        target.write_text(_render_callflow_html(data), encoding="utf-8")
    else:
        raise KeyError(fmt)


# ---------- Signed URLs ----------


def issue_signed_url(ws: Workspace, fmt: str, base_url: str) -> tuple[str, datetime]:
    """Return (relative_url, expires_at). Caller prepends base."""
    s = get_settings()
    serializer = _serializer()
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=s.graphify_url_ttl_seconds)
    token = serializer.dumps({"job": ws.job_id, "fmt": fmt})
    relative = f"/v1/graphify/artifacts/{token}"
    return relative, expires_at


def resolve_signed_url(token: str) -> tuple[Path, str, str]:
    """Return (file_path, mime, filename) for a signed token, or raise."""
    s = get_settings()
    serializer = _serializer()
    try:
        data = serializer.loads(token, max_age=s.graphify_url_ttl_seconds)
    except SignatureExpired as exc:
        raise PermissionError("signed URL expired") from exc
    except BadSignature as exc:
        raise PermissionError("invalid signed URL") from exc
    job_id = data["job"]
    fmt = data["fmt"]
    if fmt not in FORMAT_MAP:
        raise KeyError(fmt)
    fname, mime = FORMAT_MAP[fmt]
    root = s.graphify_artifact_root / job_id / fname
    if not root.exists():
        raise FileNotFoundError(f"artifact missing: {root}")
    return root, mime, fname


# ---------- Renderers (best-effort, deterministic) ----------


def _minimal_html(data: dict) -> str:
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    rows = "\n".join(
        f"<li>{_html_escape(n.get('label', n.get('id', '')))}</li>" for n in nodes[:200]
    )
    return (
        "<!doctype html><meta charset='utf-8'>"
        "<title>graph</title>"
        f"<h1>{len(nodes)} nodes / {len(edges)} edges</h1>"
        f"<ul>{rows}</ul>"
    )


def _render_svg(data: dict) -> str:
    nodes = data.get("nodes", [])[:200]
    edges = data.get("edges", [])[:400]
    w, h = 800, 600
    parts = [
        f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {w} {h}'>",
        "<style>circle{fill:#1f77b4}text{font:11px sans-serif;fill:#222}</style>",
    ]
    import math

    n = max(len(nodes), 1)
    coords = []
    for i, _node in enumerate(nodes):
        a = 2 * math.pi * i / n
        coords.append((w / 2 + 200 * math.cos(a), h / 2 + 200 * math.sin(a)))
    id_index = {node.get("id"): i for i, node in enumerate(nodes) if node.get("id")}
    for e in edges:
        s = id_index.get(e.get("source"))
        t = id_index.get(e.get("target"))
        if s is None or t is None:
            continue
        x1, y1 = coords[s]
        x2, y2 = coords[t]
        parts.append(
            f"<line x1='{x1:.1f}' y1='{y1:.1f}' x2='{x2:.1f}' y2='{y2:.1f}' "
            f"stroke='#bbb' stroke-width='0.5'/>"
        )
    for (x, y), node in zip(coords, nodes):
        parts.append(
            f"<circle cx='{x:.1f}' cy='{y:.1f}' r='3'/>"
            f"<text x='{x + 5:.1f}' y='{y + 3:.1f}'>{_html_escape(node.get('label', ''))[:30]}</text>"
        )
    parts.append("</svg>")
    return "\n".join(parts)


def _render_graphml(data: dict) -> str:
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    directed = "true" if data.get("directed", True) else "false"
    out = [
        "<?xml version='1.0' encoding='UTF-8'?>",
        f"<graphml xmlns='http://graphml.graphdrawing.org/xmlns'><graph id='g' edgedefault='{'directed' if directed == 'true' else 'undirected'}'>",
    ]
    for n in nodes:
        nid = _xml_escape(n.get("id", ""))
        label = _xml_escape(n.get("label", ""))
        out.append(f"<node id='{nid}'><data key='label'>{label}</data></node>")
    for i, e in enumerate(edges):
        s = _xml_escape(e.get("source", ""))
        t = _xml_escape(e.get("target", ""))
        out.append(f"<edge id='e{i}' source='{s}' target='{t}'/>")
    out.append("</graph></graphml>")
    return "\n".join(out)


def _render_cypher(data: dict) -> str:
    out: list[str] = []
    for n in data.get("nodes", []):
        nid = _json_str(n.get("id", ""))
        label = _json_str(n.get("label", ""))
        out.append(f"CREATE (:Node {{id: {nid}, label: {label}}});")
    for e in data.get("edges", []):
        s = _json_str(e.get("source", ""))
        t = _json_str(e.get("target", ""))
        rel = _json_str(e.get("relation", "related_to"))
        out.append(f"MATCH (a {{id: {s}}}), (b {{id: {t}}}) CREATE (a)-[:REL {{kind: {rel}}}]->(b);")
    return "\n".join(out)


def _render_wiki(data: dict) -> str:
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    by_community: dict[str, list[dict]] = {}
    for n in nodes:
        c = str(n.get("community") or "uncategorized")
        by_community.setdefault(c, []).append(n)
    out = ["# Graph Wiki", ""]
    for c in sorted(by_community):
        out.append(f"## Community {c}")
        for n in by_community[c][:200]:
            out.append(
                f"- **{n.get('label', n.get('id', ''))}** — "
                f"{_md_escape(n.get('summary', ''))} "
                f"_({_md_escape(n.get('source_file', ''))})_"
            )
        out.append("")
    out.append(f"## Edges ({len(edges)})")
    for e in edges[:500]:
        out.append(
            f"- `{e.get('source', '')}` → `{e.get('target', '')}` "
            f"({e.get('relation', '?')}, {e.get('confidence', '?')})"
        )
    return "\n".join(out)


def _render_callflow_html(data: dict) -> str:
    edges = [e for e in data.get("edges", []) if e.get("relation") == "calls"][:300]
    rows = "\n".join(
        f"<tr><td>{_html_escape(e.get('source', ''))}</td>"
        f"<td>{_html_escape(e.get('target', ''))}</td>"
        f"<td>{_html_escape(e.get('source_file', ''))}</td></tr>"
        for e in edges
    )
    return (
        "<!doctype html><meta charset='utf-8'><title>callflow</title>"
        "<table border='1' cellpadding='4' cellspacing='0'>"
        f"<tr><th>caller</th><th>callee</th><th>source_file</th></tr>{rows}</table>"
    )


def _html_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _xml_escape(s: str) -> str:
    return _html_escape(s).replace("'", "&apos;")


def _md_escape(s: str) -> str:
    return s.replace("|", "\\|")


def _json_str(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)
