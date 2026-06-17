from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import settings

_SECRET_PATTERNS = [
    re.compile(r"(api[_-]?key|token|secret|password|passwd|pwd)\s*[:=]\s*[^\s,;]+", re.I),
    re.compile(r"Bearer\s+[A-Za-z0-9._~+\-/=]+", re.I),
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
]


def redact(value: Any) -> Any:
    if isinstance(value, str):
        out = value
        for pattern in _SECRET_PATTERNS:
            out = pattern.sub(lambda m: m.group(0).split("=")[0] + "=[REDACTED]" if "=" in m.group(0) else "[REDACTED]", out)
        return out
    if isinstance(value, dict):
        return {k: ("[REDACTED]" if any(s in k.lower() for s in ["token", "key", "secret", "password"]) else redact(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value


def audit(event: str, **payload: Any) -> None:
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **redact(payload),
    }
    Path(settings.audit_log).parent.mkdir(parents=True, exist_ok=True)
    with open(settings.audit_log, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
