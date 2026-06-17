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


def write_html(graph: dict[str, Any]) -> Path:
    out = graph_path(graph["graph_id"])
    nodes = graph["nodes"][:1500]
    edges = graph["edges"][:3000]
    data = json.dumps({"nodes": nodes, "edges": edges}, ensure_ascii=False)
    body = f"""<!doctype html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\" />
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
<title>Graphify — {html.escape(graph['graph_id'])}</title>
<style>
body{{font-family:Arial,sans-serif;margin:0;background:#0b1020;color:#e8eefc}}
header{{padding:16px 20px;background:#121a33;border-bottom:1px solid #293453}}
main{{display:grid;grid-template-columns:360px 1fr;height:calc(100vh - 67px)}}
aside{{overflow:auto;border-right:1px solid #293453;padding:12px}}
section{{overflow:auto;padding:12px}}
input{{width:100%;box-sizing:border-box;padding:10px;border-radius:8px;border:1px solid #46506c;background:#10172a;color:#fff}}
.node{{padding:8px;border-bottom:1px solid #26304e;cursor:pointer}}
.node:hover{{background:#1a2444}}
.badge{{display:inline-block;font-size:11px;border:1px solid #55617f;border-radius:999px;padding:2px 6px;margin-right:6px}}
pre{{white-space:pre-wrap;background:#10172a;border:1px solid #293453;padding:12px;border-radius:8px}}
</style>
</head>
<body>
<header><b>Graphify</b> — {html.escape(graph['graph_id'])} · nodes {len(graph['nodes'])} · edges {len(graph['edges'])}</header>
<main><aside><input id=\"q\" placeholder=\"Search nodes...\"/><div id=\"list\"></div></aside><section><pre id=\"detail\">Select a node.</pre></section></main>
<script>
const graph = {data};
const list = document.getElementById('list');
const detail = document.getElementById('detail');
const q = document.getElementById('q');
function render(){{
  const term = q.value.toLowerCase();
  const nodes = graph.nodes.filter(n => !term || JSON.stringify(n).toLowerCase().includes(term)).slice(0, 250);
  list.innerHTML = nodes.map(n => `<div class=\"node\" data-id=\"${{n.id}}\"><span class=\"badge\">${{n.type}}</span>${{n.label||n.id}}<br><small>${{n.path||''}}</small></div>`).join('');
}}
list.onclick = e => {{ const item=e.target.closest('.node'); if(!item)return; const n=graph.nodes.find(x=>x.id===item.dataset.id); const es=graph.edges.filter(x=>x.source===n.id||x.target===n.id).slice(0,50); detail.textContent=JSON.stringify({{node:n,edges:es}}, null, 2); }};
q.oninput = render; render();
</script>
</body></html>"""
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
