"""Thin wrapper around the `graphify` CLI.

Each public method maps to a CLI subcommand and returns a structured result
the routes can serialize. The runner is intentionally dumb — it doesn't know
about jobs, auth, or HTTP. Errors are translated to `RunnerError` so the
caller can decide how to surface them.
"""

from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import get_settings
from .workspace import Workspace

_log = logging.getLogger("graphify.runner")


class RunnerError(Exception):
    """Raised when a graphify CLI call fails or produces no output."""


@dataclass(frozen=True)
class CmdResult:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False


def _run(args: list[str], *, timeout: int) -> CmdResult:
    """Invoke the CLI. Captures stdout/stderr; raises on non-zero exit."""
    settings = get_settings()
    cmd = [settings.graphify_cli_bin, *args]
    _log.info("exec: %s (timeout=%ss)", " ".join(cmd), timeout)
    # Force UTF-8 decode so emoji / non-ASCII output from the CLI doesn't
    # crash the parent on Windows consoles that default to cp949/cp1252.
    env = {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "LC_ALL": "C.UTF-8",
        "LANG": "C.UTF-8",
    }
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env={**__import__("os").environ, **env},
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return CmdResult(
            returncode=-1,
            stdout=(exc.stdout or "") if isinstance(exc.stdout, str) else "",
            stderr=((exc.stderr or b"").decode("utf-8", errors="replace")
                    if isinstance(exc.stderr, (bytes, bytearray)) else (exc.stderr or "")) + "\n[timeout]",
            timed_out=True,
        )
    return CmdResult(
        returncode=proc.returncode,
        stdout=proc.stdout or "",
        stderr=proc.stderr or "",
    )


def _graph_path(ws: Workspace) -> Path:
    return ws.work_dir / "corpus" / "graphify-out" / "graph.json"


# ---------- Build pipeline ----------


def _corpus_dir(ws: Workspace) -> Path:
    """Path passed to the graphify CLI. The corpus is staged in `corpus/`
    inside the workspace so it is never confused with the surrounding dir."""
    return ws.work_dir / "corpus"


def build(ws: Workspace, *, no_viz: bool, force: bool = True) -> CmdResult:
    """Run the full build pipeline: `update` + optional `cluster-only`.

    `graphify update` performs AST-based extraction and writes graph.json.
    `graphify cluster-only` adds community detection and regenerates the
    HTML visualization. We pass --force on update so a re-run replaces the
    graph even if it appears smaller (refactors that delete code).
    """
    corpus = _corpus_dir(ws)
    update_args = ["update", str(corpus)]
    if force:
        update_args.append("--force")
    update_result = _run(update_args, timeout=get_settings().graphify_max_build_seconds)
    if update_result.returncode != 0:
        return update_result

    if not no_viz:
        cluster_args = ["cluster-only", str(corpus)]
        cluster_args.append("--no-viz")  # we expose HTML via export
        cluster_result = _run(cluster_args, timeout=get_settings().graphify_max_build_seconds)
        if cluster_result.returncode != 0:
            return cluster_result
        return CmdResult(
            returncode=0,
            stdout=update_result.stdout + cluster_result.stdout,
            stderr=update_result.stderr + cluster_result.stderr,
        )
    return update_result


def update(ws: Workspace) -> CmdResult:
    """Incremental update — `graphify update --force`."""
    args = ["update", str(_corpus_dir(ws)), "--force"]
    return _run(args, timeout=get_settings().graphify_max_build_seconds)


# ---------- Query / traversal ----------


def query(
    ws: Workspace,
    question: str,
    *,
    dfs: bool,
    budget: int,
    context_filter: list[str] | None = None,
) -> CmdResult:
    args = ["query", question, "--budget", str(budget)]
    if dfs:
        args.append("--dfs")
    for ctx in context_filter or []:
        args.extend(["--context", ctx])
    args.extend(["--graph", str(_graph_path(ws))])
    return _run(args, timeout=60)


def path(ws: Workspace, source: str, target: str) -> CmdResult:
    args = ["path", source, target, "--graph", str(_graph_path(ws))]
    return _run(args, timeout=60)


def explain(ws: Workspace, label: str, depth: int) -> CmdResult:
    args = ["explain", label, "--graph", str(_graph_path(ws))]
    # The CLI doesn't expose --depth on explain; we use it as a hint only.
    _ = depth
    return _run(args, timeout=60)


def affected(
    ws: Workspace, label: str, relations: list[str], depth: int
) -> CmdResult:
    args = ["affected", label, "--depth", str(depth), "--graph", str(_graph_path(ws))]
    for r in relations:
        args.extend(["--relation", r])
    return _run(args, timeout=60)


# ---------- Stats ----------


def stats(ws: Workspace) -> dict[str, Any]:
    """Compute stats directly from graph.json (no CLI needed)."""
    gp = _graph_path(ws)
    if not gp.exists():
        raise RunnerError(f"graph.json not found at {gp}")
    try:
        data = json.loads(gp.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RunnerError(f"failed to read graph.json: {exc}") from exc

    nodes = data.get("nodes", []) or []
    # The graphify CLI emits edges under the `links` key for networkx-style
    # node-link JSON. Accept both for forward compatibility.
    edges = data.get("links") or data.get("edges") or []

    communities: set[str] = {
        n.get("community", "") for n in nodes if n.get("community")
    }
    communities.discard("")

    extracted = sum(1 for e in edges if e.get("confidence") == "EXTRACTED")
    inferred = sum(1 for e in edges if e.get("confidence") == "INFERRED")
    ambiguous = sum(1 for e in edges if e.get("confidence") == "AMBIGUOUS")
    total = max(len(edges), 1)
    extracted_pct = round(100.0 * extracted / total, 2)
    inferred_pct = round(100.0 * inferred / total, 2)
    ambiguous_pct = round(100.0 * ambiguous / total, 2)

    # Top nodes by degree (in + out).
    degree: dict[str, int] = {}
    source: dict[str, str] = {}
    for n in nodes:
        nid = n.get("id") or n.get("label")
        if nid:
            degree.setdefault(nid, 0)
            source.setdefault(nid, n.get("source_file", ""))
    for e in edges:
        s = e.get("source")
        t = e.get("target")
        if s in degree:
            degree[s] += 1
        if t in degree:
            degree[t] += 1
    top = sorted(degree.items(), key=lambda kv: kv[1], reverse=True)[:10]
    top_nodes = [
        {
            "label": nid,
            "degree": d,
            "source_file": source.get(nid, ""),
        }
        for nid, d in top
    ]

    return {
        "graph_id": ws.job_id,
        "nodes": len(nodes),
        "edges": len(edges),
        "communities": len(communities),
        "extracted_pct": extracted_pct,
        "inferred_pct": inferred_pct,
        "ambiguous_pct": ambiguous_pct,
        "top_nodes": top_nodes,
    }
