"""Query service — turns CLI output into TextResult envelopes.

The graphify CLI returns plain-text answers; the GPT Action expects a
structured envelope with `result`, `evidence`, and `warnings`. This service
is a thin adapter that:

  1. Invokes the appropriate runner method.
  2. Passes the output through unchanged as `result` (the CLI already formats
     evidence inline).
  3. Extracts `source_file:line` references from the text as `evidence`.
  4. Surfaces CLI warnings as `warnings`.
"""

from __future__ import annotations

import re
from typing import Any

from .graphify_runner import CmdResult, RunnerError, affected, explain, path, query
from .models import EvidenceItem, TextResult
from .workspace import Workspace

# Match `path/to/file.ext:123` or `path/to/file.ext line 123` style references.
_SOURCE_RE = re.compile(
    r"(?P<file>[A-Za-z0-9_./-]+\.[A-Za-z0-9]+)"
    r"(?::(?P<line>\d+))?"
    r"(?: line (?P<line2>\d+))?"
)
# Match trailing parenthetical confidence.
_CONF_RE = re.compile(r"\((?P<conf>EXTRACTED|INFERRED|AMBIGUOUS)\)")


def _extract_evidence(text: str) -> list[EvidenceItem]:
    seen: set[tuple[str, str]] = set()
    out: list[EvidenceItem] = []
    for m in _SOURCE_RE.finditer(text):
        f = m.group("file")
        line = m.group("line") or m.group("line2") or ""
        key = (f, line)
        if key in seen:
            continue
        seen.add(key)
        # Try to find a confidence near the match.
        conf = "EXTRACTED"
        nearby = text[max(0, m.start() - 30) : m.end() + 30]
        cm = _CONF_RE.search(nearby)
        if cm:
            conf = cm.group("conf")
        out.append(
            EvidenceItem(
                node=f,
                source_file=f,
                source_location=f"line {line}" if line else "",
                confidence=conf,
            )
        )
    return out


def _wrap(graph_id: str, res: CmdResult) -> TextResult:
    if res.timed_out:
        return TextResult(
            graph_id=graph_id,
            result="(timed out)",
            warnings=["graphify CLI timed out"],
        )
    if res.returncode != 0:
        msg = (res.stderr or res.stdout or "").strip()
        return TextResult(
            graph_id=graph_id,
            result=msg or "(no output)",
            warnings=[f"exit={res.returncode}"],
        )
    text = (res.stdout or "").strip()
    if not text:
        text = "(no output)"
    warnings = [ln.strip() for ln in (res.stderr or "").splitlines() if ln.strip()]
    return TextResult(
        graph_id=graph_id,
        result=text,
        evidence=_extract_evidence(text),
        warnings=warnings[:20],
    )


def run_query(
    ws: Workspace,
    *,
    question: str,
    mode: str,
    token_budget: int,
    context_filter: list[str] | None = None,
) -> TextResult:
    res = query(
        ws,
        question,
        dfs=(mode == "dfs"),
        budget=token_budget,
        context_filter=context_filter,
    )
    return _wrap(ws.job_id, res)


def run_path(ws: Workspace, *, source: str, target: str, max_hops: int) -> TextResult:
    _ = max_hops  # CLI doesn't expose max_hops; passed as a hint only
    res = path(ws, source, target)
    return _wrap(ws.job_id, res)


def run_explain(ws: Workspace, *, label: str, depth: int) -> TextResult:
    res = explain(ws, label, depth)
    return _wrap(ws.job_id, res)


def run_affected(
    ws: Workspace, *, label: str, relations: list[str], depth: int
) -> TextResult:
    res = affected(ws, label, relations, depth)
    return _wrap(ws.job_id, res)
