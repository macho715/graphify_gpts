"""Audit log — JSONL, append-only, secret/PII-redacting.

Every job lifecycle event, every CLI invocation, every signed-URL issue is
recorded. Sensitive substrings are replaced with `***` before the line is
written; the raw values are never persisted.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import get_settings

# Patterns we never want to see in the log, even after redaction.
_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),                # OpenAI/Anthropic style
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),                 # GitHub PAT
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),         # Slack
    re.compile(r"AIza[0-9A-Za-z_-]{30,}"),               # Google
    re.compile(r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}"),  # JWT-ish
    re.compile(r"AKIA[0-9A-Z]{16}"),                     # AWS access key
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)

_PII_PATTERNS: tuple[re.Pattern[str], ...] = (
    # Email addresses
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
)


def _redact(text: str) -> str:
    out = text
    for pat in _SECRET_PATTERNS:
        out = pat.sub("***REDACTED***", out)
    for pat in _PII_PATTERNS:
        out = pat.sub("[email]", out)
    return out


def _scrub(obj: Any) -> Any:
    if isinstance(obj, str):
        return _redact(obj)
    if isinstance(obj, dict):
        return {k: _scrub(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_scrub(v) for v in obj]
    if isinstance(obj, tuple):
        return tuple(_scrub(v) for v in obj)
    return obj


_log = logging.getLogger("graphify.audit")


def audit(event: str, **fields: Any) -> None:
    """Append a JSONL audit line.

    The line is built from event + fields, secret-redacted, and written to the
    configured audit log path. A copy is also emitted to stderr at INFO for
    live observability.
    """
    settings = get_settings()
    payload: dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
    }
    payload.update(fields)
    payload = _scrub(payload)
    line = json.dumps(payload, ensure_ascii=False, default=str)
    try:
        with settings.graphify_audit_log.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError as exc:
        _log.warning("audit write failed: %s", exc)
    _log.info("audit %s", line)
