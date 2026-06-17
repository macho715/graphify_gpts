from __future__ import annotations

import math
import re
from collections import defaultdict, deque
from typing import Any

WORD_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{1,}|[가-힣]{2,}")


def tokenize(value: str) -> set[str]:
    return {t.lower() for t in WORD_RE.findall(value)}


def node_text(node: dict[str, Any]) -> str:
    return " ".join(str(node.get(k, "")) for k in ["id", "label", "type", "path", "summary", "evidence"])


def find_nodes(graph: dict[str, Any], query: str, limit: int = 10, node_types: list[str] | None = None) -> list[dict[str, Any]]:
    qtokens = tokenize(query)
    if not qtokens:
        qtokens = {query.lower()}
    hits: list[dict[str, Any]] = []
    types = set(node_types or [])
    for node in graph.get("nodes", []):
        if types and node.get("type") not in types:
            continue
        text = node_text(node).lower()
        ntokens = tokenize(text)
        overlap = len(qtokens & ntokens)
        substring = sum(1 for t in qtokens if t in text)
        if overlap == 0 and substring == 0:
            continue
        score = (overlap * 2.0 + substring) / max(1.0, math.sqrt(len(ntokens) + 1))
        hits.append({
            "node_id": node["id"],
            "label": node.get("label", node["id"]),
            "type": node.get("type", "unknown"),
            "score": round(score, 4),
            "evidence": node.get("evidence") or node.get("summary"),
            "path": node.get("path"),
        })
    hits.sort(key=lambda h: h["score"], reverse=True)
    return hits[:limit]


def resolve_node_id(graph: dict[str, Any], ref: str) -> str | None:
    nodes = graph.get("nodes", [])
    by_id = {n["id"]: n for n in nodes}
    if ref in by_id:
        return ref
    low = ref.lower()
    for n in nodes:
        if str(n.get("path", "")).lower() == low or str(n.get("label", "")).lower() == low:
            return n["id"]
    hits = find_nodes(graph, ref, limit=1)
    return hits[0]["node_id"] if hits else None


def adjacency(graph: dict[str, Any]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    inc: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for e in graph.get("edges", []):
        out[e["source"]].append(e)
        inc[e["target"]].append(e)
    return out, inc


def shortest_path(graph: dict[str, Any], source_ref: str, target_ref: str, max_depth: int = 6) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes = {n["id"]: n for n in graph.get("nodes", [])}
    src = resolve_node_id(graph, source_ref)
    dst = resolve_node_id(graph, target_ref)
    if not src or not dst:
        return [], []
    out, inc = adjacency(graph)
    q = deque([(src, [src], [])])
    seen = {src}
    while q:
        current, path, edges = q.popleft()
        if current == dst:
            return [nodes[n] for n in path if n in nodes], edges
        if len(path) - 1 >= max_depth:
            continue
        for e in out.get(current, []) + inc.get(current, []):
            nxt = e["target"] if e["source"] == current else e["source"]
            if nxt in seen:
                continue
            seen.add(nxt)
            q.append((nxt, path + [nxt], edges + [e]))
    return [], []


def explain_node(graph: dict[str, Any], node_id: str | None = None, query: str | None = None, depth: int = 1) -> dict[str, Any]:
    nodes = {n["id"]: n for n in graph.get("nodes", [])}
    if not node_id and query:
        node_id = resolve_node_id(graph, query)
    if not node_id or node_id not in nodes:
        return {"node": None, "neighbors": [], "evidence": [], "summary": "No matching node found."}
    out, inc = adjacency(graph)
    center = nodes[node_id]
    q = deque([(node_id, 0)])
    seen = {node_id}
    neighbor_ids: list[str] = []
    rel_edges: list[dict[str, Any]] = []
    while q:
        current, d = q.popleft()
        if d >= depth:
            continue
        for e in out.get(current, []) + inc.get(current, []):
            nxt = e["target"] if e["source"] == current else e["source"]
            rel_edges.append(e)
            if nxt not in seen:
                seen.add(nxt)
                neighbor_ids.append(nxt)
                q.append((nxt, d + 1))
    neighbors = [nodes[n] for n in neighbor_ids if n in nodes][:80]
    evidence = [center.get("evidence") or center.get("summary") or ""]
    evidence.extend([e.get("evidence", "") for e in rel_edges[:20] if e.get("evidence")])
    summary = f"{center.get('label', node_id)} is a {center.get('type', 'node')} with {len(neighbors)} neighbor nodes within depth {depth}."
    return {"node": center, "neighbors": neighbors, "evidence": evidence[:30], "summary": summary}


def affected_nodes(graph: dict[str, Any], node_id: str | None = None, query: str | None = None, direction: str = "both", max_depth: int = 2, limit: int = 50) -> dict[str, Any]:
    nodes = {n["id"]: n for n in graph.get("nodes", [])}
    if not node_id and query:
        node_id = resolve_node_id(graph, query)
    if not node_id or node_id not in nodes:
        return {"start_node": None, "affected": [], "edges": []}
    out, inc = adjacency(graph)
    q = deque([(node_id, 0)])
    seen = {node_id}
    affected: list[str] = []
    edges: list[dict[str, Any]] = []
    while q and len(affected) < limit:
        current, depth = q.popleft()
        if depth >= max_depth:
            continue
        candidates: list[dict[str, Any]] = []
        if direction in {"out", "both"}:
            candidates += out.get(current, [])
        if direction in {"in", "both"}:
            candidates += inc.get(current, [])
        for e in candidates:
            nxt = e["target"] if e["source"] == current else e["source"]
            if nxt in seen:
                continue
            seen.add(nxt)
            affected.append(nxt)
            edges.append(e)
            q.append((nxt, depth + 1))
            if len(affected) >= limit:
                break
    return {"start_node": nodes[node_id], "affected": [nodes[n] for n in affected if n in nodes], "edges": edges}
