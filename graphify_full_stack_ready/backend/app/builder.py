from __future__ import annotations

import ast
import fnmatch
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import textwrap
import time
import urllib.request
import zipfile
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .audit import audit
from .config import settings
from .models import BuildRequest, GraphifySource
from .security import redact_inline_secrets, should_skip, validate_public_url

WORD_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{1,}|[가-힣]{2,}")
JS_DEF_RE = re.compile(r"\b(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)|\bclass\s+([A-Za-z_$][\w$]*)|\bconst\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\(?")
JS_IMPORT_RE = re.compile(r"(?:from\s+['\"]([^'\"]+)['\"]|import\s+['\"]([^'\"]+)['\"]|require\(['\"]([^'\"]+)['\"]\))")
MD_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def slug(value: str, max_len: int = 90) -> str:
    clean = re.sub(r"[^a-zA-Z0-9_.-]+", "-", value).strip("-_.").lower()
    return (clean or "graph")[:max_len]


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="ignore")).hexdigest()


def make_graph_id(source: GraphifySource, requested: str | None = None) -> str:
    if requested:
        return slug(requested)
    raw = source.url or source.path or "inline"
    return f"graph-{slug(raw)}-{sha256_text(raw)[:8]}"


def prepare_workspace(job_id: str, request: BuildRequest) -> Path:
    workspace = settings.work_dir / job_id
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    src = workspace / "src"
    source = request.source
    if source.type == "inline_files":
        src.mkdir(parents=True, exist_ok=True)
        if not source.files:
            raise ValueError("inline_files source requires files")
        for item in source.files:
            rel = Path(item.path.replace("\\", "/"))
            if rel.is_absolute() or ".." in rel.parts:
                raise ValueError(f"Unsafe inline file path: {item.path}")
            target = src / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(item.content, encoding="utf-8")
        audit("source.inline_files.materialized", job_id=job_id, file_count=len(source.files))
        return src
    if source.type == "local_path":
        if not settings.allow_local_path:
            raise ValueError("local_path source disabled. Set GRAPHIFY_ALLOW_LOCAL_PATH=true for trusted local tests.")
        if not source.path:
            raise ValueError("local_path source requires path")
        path = Path(source.path).resolve()
        if not path.exists():
            raise ValueError(f"local_path not found: {path}")
        if path.is_file() and path.suffix.lower() == ".zip":
            with zipfile.ZipFile(path) as zf:
                safe_extract_zip(zf, src)
        elif path.is_dir():
            shutil.copytree(path, src, ignore=shutil.ignore_patterns(".git", "node_modules", "__pycache__", ".venv"))
        else:
            src.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, src / path.name)
        audit("source.local_path.materialized", job_id=job_id, path=str(path))
        return normalize_single_root(src)
    if source.type == "zip_url":
        if not source.url:
            raise ValueError("zip_url source requires url")
        validate_public_url(source.url)
        zip_path = workspace / "source.zip"
        urllib.request.urlretrieve(source.url, zip_path)  # noqa: S310 - validate_public_url blocks local/non-https hosts.
        with zipfile.ZipFile(zip_path) as zf:
            safe_extract_zip(zf, src)
        audit("source.zip_url.materialized", job_id=job_id, url=source.url)
        return normalize_single_root(src)
    if source.type == "git":
        if not source.url:
            raise ValueError("git source requires url")
        validate_public_url(source.url)
        cmd = ["git", "clone", "--depth", "1"]
        if source.branch:
            cmd.extend(["--branch", source.branch])
        cmd.extend([source.url, str(src)])
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=settings.clone_timeout_seconds, check=False)
        audit("source.git.clone", job_id=job_id, url=source.url, branch=source.branch, returncode=result.returncode, stderr=result.stderr[-500:])
        if result.returncode != 0:
            raise RuntimeError(f"git clone failed: {result.stderr[-1000:]}")
        return src
    raise ValueError(f"Unsupported source type: {source.type}")


def safe_extract_zip(zf: zipfile.ZipFile, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    for member in zf.infolist():
        target = (destination / member.filename).resolve()
        if root not in target.parents and target != root:
            raise ValueError(f"Unsafe ZIP member path: {member.filename}")
        zf.extract(member, destination)


def normalize_single_root(path: Path) -> Path:
    children = [p for p in path.iterdir() if p.name not in {"__MACOSX"}]
    if len(children) == 1 and children[0].is_dir():
        return children[0]
    return path


def include_file(rel: str, include_patterns: list[str], exclude_patterns: list[str]) -> bool:
    if include_patterns and not any(fnmatch.fnmatch(rel, pat) for pat in include_patterns):
        return False
    if exclude_patterns and any(fnmatch.fnmatch(rel, pat) for pat in exclude_patterns):
        return False
    return True


def read_text(path: Path) -> str:
    data = path.read_bytes()
    if b"\x00" in data[:4096]:
        raise UnicodeDecodeError("binary", b"", 0, 1, "NUL byte detected")
    for enc in ["utf-8", "utf-8-sig", "cp949", "latin-1"]:
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def tokens(text: str) -> list[str]:
    return [t.lower() for t in WORD_RE.findall(text)]


def add_node(graph: dict[str, Any], node: dict[str, Any]) -> None:
    node.setdefault("tokens", tokens(" ".join(str(node.get(k, "")) for k in ["id", "label", "type", "path", "summary", "evidence"])))
    graph["nodes"][node["id"]] = node


def add_edge(graph: dict[str, Any], source: str, target: str, relation: str, evidence: str | None = None) -> None:
    if source == target:
        return
    edge_id = sha256_text(f"{source}|{relation}|{target}|{evidence or ''}")[:16]
    edge = {"id": edge_id, "source": source, "target": target, "relation": relation}
    if evidence:
        edge["evidence"] = evidence[:500]
    graph["edges"].append(edge)


def build_graph_from_source(job_id: str, request: BuildRequest) -> dict[str, Any]:
    start = time.time()
    root = prepare_workspace(job_id, request)
    graph_id = make_graph_id(request.source, request.options.graph_id)
    max_files = request.options.max_files or settings.max_files
    graph: dict[str, Any] = {
        "schema_version": "graphify-gpts-fullstack/v1",
        "graph_id": graph_id,
        "generated_at": utc_now(),
        "source": request.source.model_dump(exclude={"files"}),
        "options": request.options.model_dump(),
        "nodes": {},
        "edges": [],
        "skipped_files": [],
        "redactions": 0,
        "meta": {"builder": "deterministic-local", "job_id": job_id},
    }
    project_node = {
        "id": "project:root",
        "type": "project",
        "label": root.name,
        "path": ".",
        "summary": "Repository/project root",
        "evidence": str(root),
    }
    add_node(graph, project_node)
    total_bytes = 0
    files_processed = 0
    file_texts: dict[str, str] = {}
    path_to_node: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if not include_file(rel, request.options.include_patterns, request.options.exclude_patterns):
            graph["skipped_files"].append({"path": rel, "reason": "pattern_excluded"})
            continue
        skip, reason = should_skip(path, root)
        if skip:
            graph["skipped_files"].append({"path": rel, "reason": reason})
            continue
        if files_processed >= max_files:
            graph["skipped_files"].append({"path": rel, "reason": "max_files_reached"})
            continue
        size = path.stat().st_size
        total_bytes += size
        if total_bytes > settings.max_total_bytes:
            graph["skipped_files"].append({"path": rel, "reason": "max_total_bytes_reached"})
            continue
        try:
            text = read_text(path)
        except Exception as exc:
            graph["skipped_files"].append({"path": rel, "reason": f"read_failed:{exc.__class__.__name__}"})
            continue
        text, redactions = redact_inline_secrets(text)
        graph["redactions"] += redactions
        files_processed += 1
        node_id = f"file:{rel}"
        file_texts[rel] = text
        path_to_node[rel] = node_id
        first_lines = "\n".join([ln.strip() for ln in text.splitlines()[:8] if ln.strip()])[:500]
        node = {
            "id": node_id,
            "type": "file",
            "label": Path(rel).name,
            "path": rel,
            "size_bytes": size,
            "sha256": hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest(),
            "summary": summarize_text(text),
            "evidence": first_lines,
        }
        add_node(graph, node)
        add_edge(graph, "project:root", node_id, "CONTAINS", rel)
        add_folder_edges(graph, rel, node_id)
        parse_file_symbols(graph, rel, text)
    link_local_imports(graph, file_texts, path_to_node)
    graph["nodes"] = list(graph["nodes"].values())
    graph["stats"] = compute_stats(graph)
    graph["meta"]["elapsed_seconds"] = round(time.time() - start, 3)
    persist_graph(graph)
    write_report(graph)
    write_html(graph)
    audit("graph.build.completed", job_id=job_id, graph_id=graph_id, stats=graph["stats"])
    return graph


def add_folder_edges(graph: dict[str, Any], rel: str, file_node: str) -> None:
    parts = Path(rel).parts[:-1]
    parent = "project:root"
    acc: list[str] = []
    for part in parts:
        acc.append(part)
        path = "/".join(acc)
        folder_id = f"dir:{path}"
        if folder_id not in graph["nodes"]:
            add_node(graph, {"id": folder_id, "type": "directory", "label": part, "path": path, "summary": "Directory"})
            add_edge(graph, parent, folder_id, "CONTAINS", path)
        parent = folder_id
    if parent != "project:root":
        add_edge(graph, parent, file_node, "CONTAINS", rel)


def summarize_text(text: str, limit: int = 220) -> str:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return "Empty text file"
    candidate = " ".join(lines[:4])
    candidate = re.sub(r"\s+", " ", candidate)
    return candidate[:limit]


def parse_file_symbols(graph: dict[str, Any], rel: str, text: str) -> None:
    suffix = Path(rel).suffix.lower()
    if suffix == ".py":
        parse_python(graph, rel, text)
    elif suffix in {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}:
        parse_js(graph, rel, text)
    elif suffix in {".md", ".mdx", ".rst"}:
        parse_markdown(graph, rel, text)
    elif suffix in {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg"}:
        config_id = f"config:{rel}"
        add_node(graph, {"id": config_id, "type": "config", "label": Path(rel).name, "path": rel, "summary": "Configuration file", "evidence": summarize_text(text)})
        add_edge(graph, f"file:{rel}", config_id, "DECLARES_CONFIG", rel)


def parse_python(graph: dict[str, Any], rel: str, text: str) -> None:
    file_id = f"file:{rel}"
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        add_node(graph, {"id": f"syntax:{rel}", "type": "syntax_warning", "label": Path(rel).name, "path": rel, "summary": str(exc), "evidence": str(exc)})
        add_edge(graph, file_id, f"syntax:{rel}", "HAS_WARNING", str(exc))
        return
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            nid = f"symbol:{rel}:{node.name}"
            add_node(graph, {"id": nid, "type": "function", "label": node.name, "path": rel, "line": node.lineno, "summary": ast.get_docstring(node) or f"Python function {node.name}", "evidence": f"def {node.name}(...) line {node.lineno}"})
            add_edge(graph, file_id, nid, "DEFINES", f"line {node.lineno}")
        elif isinstance(node, ast.ClassDef):
            nid = f"symbol:{rel}:{node.name}"
            add_node(graph, {"id": nid, "type": "class", "label": node.name, "path": rel, "line": node.lineno, "summary": ast.get_docstring(node) or f"Python class {node.name}", "evidence": f"class {node.name} line {node.lineno}"})
            add_edge(graph, file_id, nid, "DEFINES", f"line {node.lineno}")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                nid = f"external:{name}"
                add_node(graph, {"id": nid, "type": "external_import", "label": name, "summary": "Imported Python module", "evidence": f"import {name}"})
                add_edge(graph, file_id, nid, "IMPORTS", f"line {getattr(node, 'lineno', '?')}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:
                module = "." * node.level + module
            nid = f"external:{module or 'relative'}"
            add_node(graph, {"id": nid, "type": "external_import", "label": module or "relative", "summary": "Imported Python module", "evidence": f"from {module} import ..."})
            add_edge(graph, file_id, nid, "IMPORTS", f"line {getattr(node, 'lineno', '?')}")


def parse_js(graph: dict[str, Any], rel: str, text: str) -> None:
    file_id = f"file:{rel}"
    for m in JS_DEF_RE.finditer(text):
        name = next((g for g in m.groups() if g), None)
        if not name:
            continue
        line = text.count("\n", 0, m.start()) + 1
        ntype = "class" if text[m.start():m.end()].strip().startswith("class") else "function"
        nid = f"symbol:{rel}:{name}"
        add_node(graph, {"id": nid, "type": ntype, "label": name, "path": rel, "line": line, "summary": f"JavaScript/TypeScript {ntype} {name}", "evidence": f"{name} line {line}"})
        add_edge(graph, file_id, nid, "DEFINES", f"line {line}")
    for m in JS_IMPORT_RE.finditer(text):
        name = next((g for g in m.groups() if g), None)
        if not name:
            continue
        line = text.count("\n", 0, m.start()) + 1
        nid = f"external:{name}"
        add_node(graph, {"id": nid, "type": "external_import", "label": name, "summary": "Imported JS/TS module", "evidence": f"import {name}"})
        add_edge(graph, file_id, nid, "IMPORTS", f"line {line}")


def parse_markdown(graph: dict[str, Any], rel: str, text: str) -> None:
    file_id = f"file:{rel}"
    for i, line in enumerate(text.splitlines(), start=1):
        m = MD_HEADING_RE.match(line)
        if not m:
            continue
        title = m.group(2).strip()[:140]
        nid = f"concept:{rel}:{slug(title, 60)}"
        add_node(graph, {"id": nid, "type": "concept", "label": title, "path": rel, "line": i, "summary": f"Markdown heading level {len(m.group(1))}: {title}", "evidence": line.strip()})
        add_edge(graph, file_id, nid, "MENTIONS_CONCEPT", f"line {i}")


def link_local_imports(graph: dict[str, Any], file_texts: dict[str, str], path_to_node: dict[str, str]) -> None:
    rels = list(path_to_node)
    stem_index: dict[str, list[str]] = defaultdict(list)
    for rel in rels:
        stem_index[Path(rel).stem].append(rel)
    node_lookup = {node["id"]: node for node in graph["nodes"].values()}
    for rel, text in file_texts.items():
        file_id = f"file:{rel}"
        for imported in re.findall(r"(?:from|import)\s+([A-Za-z0-9_./-]+)", text)[:80]:
            candidate_name = imported.split(".")[-1].split("/")[-1]
            for target_rel in stem_index.get(candidate_name, [])[:3]:
                if target_rel != rel:
                    add_edge(graph, file_id, f"file:{target_rel}", "REFERENCES_LOCAL", imported)


def compute_stats(graph: dict[str, Any]) -> dict[str, int]:
    nodes = graph["nodes"] if isinstance(graph["nodes"], list) else list(graph["nodes"].values())
    return {
        "nodes": len(nodes),
        "edges": len(graph["edges"]),
        "files": sum(1 for n in nodes if n.get("type") == "file"),
        "symbols": sum(1 for n in nodes if n.get("type") in {"function", "class", "concept", "config"}),
        "skipped_files": len(graph.get("skipped_files", [])),
    }


def graph_path(graph_id: str) -> Path:
    return settings.graph_dir / graph_id


def persist_graph(graph: dict[str, Any]) -> None:
    out = graph_path(graph["graph_id"])
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "graph.json", "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)


def load_graph(graph_id: str) -> dict[str, Any]:
    path = graph_path(graph_id) / "graph.json"
    if not path.exists():
        raise FileNotFoundError(f"Graph not found: {graph_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_report(graph: dict[str, Any]) -> Path:
    out = graph_path(graph["graph_id"])
    nodes = graph["nodes"]
    type_counts = Counter(n.get("type", "unknown") for n in nodes)
    top_files = [n for n in nodes if n.get("type") == "file"][:20]
    lines = [
        f"# GRAPH_REPORT — {graph['graph_id']}",
        "",
        f"- Generated: {graph['generated_at']}",
        f"- Nodes: {len(nodes)}",
        f"- Edges: {len(graph['edges'])}",
        f"- Files: {graph['stats']['files']}",
        f"- Symbols/Concepts: {graph['stats']['symbols']}",
        f"- Skipped files: {graph['stats']['skipped_files']}",
        "",
        "## Node Type Summary",
        "",
    ]
    for k, v in sorted(type_counts.items()):
        lines.append(f"- {k}: {v}")
    lines.extend(["", "## Key Files", ""])
    for n in top_files:
        lines.append(f"- `{n.get('path')}` — {n.get('summary','')[:160]}")
    lines.extend([
        "",
        "## Suggested Questions",
        "",
        "1. Which files define the main functions/classes?",
        "2. What nodes are affected if a selected file changes?",
        "3. What path connects two symbols or files?",
        "4. Which config files control runtime/deployment?",
        "",
        "## ZERO / Security Notes",
        "",
        "- Sensitive filenames and common credential paths are skipped.",
        "- Inline secret-like strings are redacted before graph persistence.",
    ])
    target = out / "GRAPH_REPORT.md"
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


# Tableau 20 palette — community colors (matches upstream Graphify visual style).
_PALETTE = [
    "#4E79A7", "#F28E2B", "#E15759", "#76B7B2", "#59A14F",
    "#EDC948", "#B07AA1", "#FF9DA7", "#9C755F", "#BAB0AC",
    "#86BCB6", "#D37295", "#FABFD2", "#B6992D", "#499894",
    "#D7B5A6", "#79706E", "#8CD17D", "#F1CE63", "#A0CBE8",
]


def _communities_and_degree(
    node_ids: list[str], edges: list[dict[str, Any]]
) -> tuple[dict[str, int], dict[str, int], list[list[str]]]:
    """Deterministic label-propagation community detection + undirected degree.

    Returns (community_id_per_node, degree_per_node, groups_ordered_by_size_desc).
    Pure Python (no networkx) so the Docker image stays dependency-light.
    """
    idset = set(node_ids)
    adj: dict[str, set[str]] = defaultdict(set)
    degree: dict[str, int] = defaultdict(int)
    for edge in edges:
        s, t = edge.get("source"), edge.get("target")
        if s in idset and t in idset and s != t:
            adj[s].add(t)
            adj[t].add(s)
            degree[s] += 1
            degree[t] += 1

    label = {nid: nid for nid in node_ids}
    order = sorted(node_ids)
    for _ in range(20):
        changed = False
        for nid in order:
            neighbors = adj.get(nid)
            if not neighbors:
                continue
            counts = Counter(label[x] for x in neighbors)
            top = max(counts.values())
            best = min(lbl for lbl, c in counts.items() if c == top)  # deterministic tie-break
            if label[nid] != best:
                label[nid] = best
                changed = True
        if not changed:
            break

    groups: dict[str, list[str]] = defaultdict(list)
    for nid, lbl in label.items():
        groups[lbl].append(nid)
    ordered = sorted(groups.values(), key=lambda g: (-len(g), sorted(g)[0]))
    cid_of = {nid: cid for cid, grp in enumerate(ordered) for nid in grp}
    return cid_of, dict(degree), ordered


# vis-network visualization template (upstream Graphify style). Data is injected
# via __PLACEHOLDER__ tokens so the literal JS braces need no f-string escaping.
_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>graphify - __TITLE__</title>
<script src="https://unpkg.com/vis-network@9.1.6/standalone/umd/vis-network.min.js"></script>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #0f0f1a; color: #e0e0e0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; display: flex; height: 100vh; overflow: hidden; }
  #graph { flex: 1; }
  #sidebar { width: 280px; background: #1a1a2e; border-left: 1px solid #2a2a4e; display: flex; flex-direction: column; overflow: hidden; }
  #search-wrap { padding: 12px; border-bottom: 1px solid #2a2a4e; }
  #search { width: 100%; background: #0f0f1a; border: 1px solid #3a3a5e; color: #e0e0e0; padding: 7px 10px; border-radius: 6px; font-size: 13px; outline: none; }
  #search:focus { border-color: #4E79A7; }
  #search-results { max-height: 140px; overflow-y: auto; padding: 4px 12px; border-bottom: 1px solid #2a2a4e; display: none; }
  .search-item { padding: 4px 6px; cursor: pointer; border-radius: 4px; font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .search-item:hover { background: #2a2a4e; }
  #info-panel { padding: 14px; border-bottom: 1px solid #2a2a4e; min-height: 140px; }
  #info-panel h3 { font-size: 13px; color: #aaa; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.05em; }
  #info-content { font-size: 13px; color: #ccc; line-height: 1.6; }
  #info-content .field { margin-bottom: 5px; }
  #info-content .field b { color: #e0e0e0; }
  #info-content .empty { color: #555; font-style: italic; }
  .neighbor-link { display: block; padding: 2px 6px; margin: 2px 0; border-radius: 3px; cursor: pointer; font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; border-left: 3px solid #333; }
  .neighbor-link:hover { background: #2a2a4e; }
  #neighbors-list { max-height: 160px; overflow-y: auto; margin-top: 4px; }
  #legend-wrap { flex: 1; overflow-y: auto; padding: 12px; }
  #legend-wrap h3 { font-size: 13px; color: #aaa; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.05em; }
  .legend-item { display: flex; align-items: center; gap: 8px; padding: 4px 0; cursor: pointer; border-radius: 4px; font-size: 12px; }
  .legend-item:hover { background: #2a2a4e; padding-left: 4px; }
  .legend-item.dimmed { opacity: 0.35; }
  .legend-dot { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }
  .legend-label { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .legend-count { color: #666; font-size: 11px; }
  #stats { padding: 10px 14px; border-top: 1px solid #2a2a4e; font-size: 11px; color: #555; }
  #legend-controls { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; padding: 4px 0; }
  #legend-controls label { display: flex; align-items: center; gap: 6px; cursor: pointer; font-size: 12px; color: #aaa; user-select: none; }
  .legend-cb, #select-all-cb { appearance: none; -webkit-appearance: none; width: 14px; height: 14px; border: 1.5px solid #3a3a5e; border-radius: 3px; background: #0f0f1a; cursor: pointer; position: relative; flex-shrink: 0; }
  .legend-cb:checked, #select-all-cb:checked { background: #4E79A7; border-color: #4E79A7; }
  .legend-cb:checked::after, #select-all-cb:checked::after { content: ''; position: absolute; left: 3.5px; top: 1px; width: 4px; height: 7px; border: solid #fff; border-width: 0 2px 2px 0; transform: rotate(45deg); }
  #select-all-cb:indeterminate { background: #4E79A7; border-color: #4E79A7; }
  #select-all-cb:indeterminate::after { content: ''; position: absolute; left: 2px; top: 5px; width: 8px; height: 2px; background: #fff; }
</style>
</head>
<body>
<div id="graph"></div>
<div id="sidebar">
  <div id="search-wrap">
    <input id="search" type="text" placeholder="Search nodes..." autocomplete="off">
    <div id="search-results"></div>
  </div>
  <div id="info-panel">
    <h3>Node Info</h3>
    <div id="info-content"><span class="empty">Click a node to inspect it</span></div>
  </div>
  <div id="legend-wrap">
    <h3>Communities</h3>
    <div id="legend-controls">
      <label><input type="checkbox" id="select-all-cb" checked onchange="toggleAllCommunities(!this.checked)">Select All</label>
    </div>
    <div id="legend"></div>
  </div>
  <div id="stats">__STATS__</div>
</div>
<script>
const RAW_NODES = __RAW_NODES__;
const RAW_EDGES = __RAW_EDGES__;
const LEGEND = __LEGEND__;
function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }

const nodesDS = new vis.DataSet(RAW_NODES.map(n => ({
  id: n.id, label: n.label, color: n.color, size: n.size,
  font: n.font, title: n.title,
  _community: n.community, _community_name: n.community_name,
  _source_file: n.source_file, _file_type: n.file_type, _degree: n.degree,
})));

const edgesDS = new vis.DataSet(RAW_EDGES.map((e, i) => ({
  id: i, from: e.from, to: e.to,
  label: '',
  title: e.title,
  width: e.width,
  color: e.color,
  arrows: { to: { enabled: true, scaleFactor: 0.5 } },
})));

const container = document.getElementById('graph');
const network = new vis.Network(container, { nodes: nodesDS, edges: edgesDS }, {
  physics: {
    enabled: true,
    solver: 'forceAtlas2Based',
    forceAtlas2Based: {
      gravitationalConstant: -60,
      centralGravity: 0.005,
      springLength: 120,
      springConstant: 0.08,
      damping: 0.4,
      avoidOverlap: 0.8,
    },
    stabilization: { iterations: 200, fit: true },
  },
  interaction: { hover: true, tooltipDelay: 100, hideEdgesOnDrag: true, navigationButtons: false, keyboard: false },
  nodes: { shape: 'dot', borderWidth: 1.5 },
  edges: { smooth: { type: 'continuous', roundness: 0.2 }, selectionWidth: 3 },
});

network.once('stabilizationIterationsDone', () => {
  network.setOptions({ physics: { enabled: false } });
});

function showInfo(nodeId) {
  const n = nodesDS.get(nodeId);
  if (!n) return;
  const neighborIds = network.getConnectedNodes(nodeId);
  const neighborItems = neighborIds.map(nid => {
    const nb = nodesDS.get(nid);
    const color = nb ? nb.color.background : '#555';
    return `<span class="neighbor-link" style="border-left-color:${esc(color)}" onclick="focusNode(${JSON.stringify(nid)})">${esc(nb ? nb.label : nid)}</span>`;
  }).join('');
  document.getElementById('info-content').innerHTML = `
    <div class="field"><b>${esc(n.label)}</b></div>
    <div class="field">Type: ${esc(n._file_type || 'unknown')}</div>
    <div class="field">Community: ${esc(n._community_name)}</div>
    <div class="field">Source: ${esc(n._source_file || '-')}</div>
    <div class="field">Degree: ${n._degree}</div>
    ${neighborIds.length ? `<div class="field" style="margin-top:8px;color:#aaa;font-size:11px">Neighbors (${neighborIds.length})</div><div id="neighbors-list">${neighborItems}</div>` : ''}
  `;
}

function focusNode(nodeId) {
  network.focus(nodeId, { scale: 1.4, animation: true });
  network.selectNodes([nodeId]);
  showInfo(nodeId);
}

let hoveredNodeId = null;
network.on('hoverNode', params => { hoveredNodeId = params.node; container.style.cursor = 'pointer'; });
network.on('blurNode', () => { hoveredNodeId = null; container.style.cursor = 'default'; });
network.on('click', params => {
  if (params.nodes.length > 0) {
    showInfo(params.nodes[0]);
  } else {
    document.getElementById('info-content').innerHTML = '<span class="empty">Click a node to inspect it</span>';
  }
});

const searchInput = document.getElementById('search');
const searchResults = document.getElementById('search-results');
searchInput.addEventListener('input', () => {
  const q = searchInput.value.toLowerCase().trim();
  searchResults.innerHTML = '';
  if (!q) { searchResults.style.display = 'none'; return; }
  const matches = RAW_NODES.filter(n => n.label.toLowerCase().includes(q)).slice(0, 20);
  if (!matches.length) { searchResults.style.display = 'none'; return; }
  searchResults.style.display = 'block';
  matches.forEach(n => {
    const el = document.createElement('div');
    el.className = 'search-item';
    el.textContent = n.label;
    el.style.borderLeft = `3px solid ${n.color.background}`;
    el.style.paddingLeft = '8px';
    el.onclick = () => {
      network.focus(n.id, { scale: 1.5, animation: true });
      network.selectNodes([n.id]);
      showInfo(n.id);
      searchResults.style.display = 'none';
      searchInput.value = '';
    };
    searchResults.appendChild(el);
  });
});
document.addEventListener('click', e => {
  if (!searchResults.contains(e.target) && e.target !== searchInput) searchResults.style.display = 'none';
});

const hiddenCommunities = new Set();
const selectAllCb = document.getElementById('select-all-cb');
function updateSelectAllState() {
  const total = LEGEND.length;
  const hidden = hiddenCommunities.size;
  selectAllCb.checked = hidden === 0;
  selectAllCb.indeterminate = hidden > 0 && hidden < total;
}
function toggleAllCommunities(hide) {
  document.querySelectorAll('.legend-item').forEach(item => { hide ? item.classList.add('dimmed') : item.classList.remove('dimmed'); });
  document.querySelectorAll('.legend-cb').forEach(cb => { cb.checked = !hide; });
  LEGEND.forEach(c => { if (hide) hiddenCommunities.add(c.cid); else hiddenCommunities.delete(c.cid); });
  nodesDS.update(RAW_NODES.map(n => ({ id: n.id, hidden: hide })));
  updateSelectAllState();
}

const legendEl = document.getElementById('legend');
LEGEND.forEach(c => {
  const item = document.createElement('div');
  item.className = 'legend-item';
  const cb = document.createElement('input');
  cb.type = 'checkbox';
  cb.className = 'legend-cb';
  cb.checked = true;
  cb.addEventListener('change', (e) => {
    e.stopPropagation();
    if (cb.checked) { hiddenCommunities.delete(c.cid); item.classList.remove('dimmed'); }
    else { hiddenCommunities.add(c.cid); item.classList.add('dimmed'); }
    nodesDS.update(RAW_NODES.filter(n => n.community === c.cid).map(n => ({ id: n.id, hidden: !cb.checked })));
    updateSelectAllState();
  });
  item.innerHTML = `<div class="legend-dot" style="background:${c.color}"></div>
    <span class="legend-label">${esc(c.label)}</span>
    <span class="legend-count">${c.count}</span>`;
  item.prepend(cb);
  item.onclick = (e) => { if (e.target === cb) return; cb.checked = !cb.checked; cb.dispatchEvent(new Event('change')); };
  legendEl.appendChild(item);
});
</script>
</body>
</html>"""


def write_html(graph: dict[str, Any]) -> Path:
    out = graph_path(graph["graph_id"])
    nodes = graph["nodes"][:1500]
    edges = graph["edges"][:3000]

    node_ids = [n["id"] for n in nodes]
    cid_of, degree, groups = _communities_and_degree(node_ids, edges)

    def _color(cid: int) -> str:
        return _PALETTE[cid % len(_PALETTE)]

    # Community display name: highest-degree node's label in that group.
    community_name: dict[int, str] = {}
    for cid, grp in enumerate(groups):
        top = max(grp, key=lambda nid: (degree.get(nid, 0), nid))
        node_label = next((n.get("label") or n["id"] for n in nodes if n["id"] == top), top)
        community_name[cid] = f"{node_label}"

    raw_nodes = []
    for n in nodes:
        nid = n["id"]
        cid = cid_of.get(nid, 0)
        deg = degree.get(nid, 0)
        bg = _color(cid)
        raw_nodes.append({
            "id": nid,
            "label": n.get("label") or nid,
            "color": {"background": bg, "border": bg, "highlight": {"background": "#ffffff", "border": bg}},
            "size": round(8 + min(deg, 40) * 0.6, 1),
            "font": {"size": 0, "color": "#ffffff"},
            "title": n.get("label") or nid,
            "community": cid,
            "community_name": community_name.get(cid, f"Community {cid}"),
            "source_file": n.get("path") or "",
            "file_type": n.get("type") or "unknown",
            "degree": deg,
        })

    raw_edges = []
    for e in edges:
        if e.get("source") not in cid_of or e.get("target") not in cid_of:
            continue
        raw_edges.append({
            "from": e["source"],
            "to": e["target"],
            "title": e.get("relation") or "",
            "width": 1,
            "color": {"color": "#55617f", "opacity": 0.45, "highlight": "#e0e0e0"},
        })

    legend = [
        {"cid": cid, "color": _color(cid), "label": community_name.get(cid, f"Community {cid}"), "count": len(grp)}
        for cid, grp in enumerate(groups)
    ]

    stats = f"{len(nodes)} nodes &middot; {len(raw_edges)} edges &middot; {len(groups)} communities"
    body = (
        _HTML_TEMPLATE
        .replace("__TITLE__", html.escape(graph["graph_id"]))
        .replace("__STATS__", stats)
        .replace("__RAW_NODES__", json.dumps(raw_nodes, ensure_ascii=False))
        .replace("__RAW_EDGES__", json.dumps(raw_edges, ensure_ascii=False))
        .replace("__LEGEND__", json.dumps(legend, ensure_ascii=False))
    )
    target = out / "graph.html"
    target.write_text(body, encoding="utf-8")
    return target


def create_export(graph_id: str, fmt: str) -> Path:
    base = graph_path(graph_id)
    if not base.exists():
        raise FileNotFoundError(f"Graph not found: {graph_id}")
    artifact_base = settings.artifact_dir / graph_id
    artifact_base.mkdir(parents=True, exist_ok=True)
    if fmt == "json":
        target = artifact_base / "graph.json"
        shutil.copy2(base / "graph.json", target)
        return target
    if fmt == "report":
        target = artifact_base / "GRAPH_REPORT.md"
        shutil.copy2(base / "GRAPH_REPORT.md", target)
        return target
    if fmt == "html":
        target = artifact_base / "graph.html"
        shutil.copy2(base / "graph.html", target)
        return target
    if fmt == "zip":
        target = artifact_base / "graphify-out.zip"
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
            for name in ["graph.json", "GRAPH_REPORT.md", "graph.html"]:
                zf.write(base / name, arcname=name)
        return target
    raise ValueError(f"Unsupported export format: {fmt}")
