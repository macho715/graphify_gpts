from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from .config import settings


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _unb64(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def sign_artifact(graph_id: str, fmt: str, file_path: Path) -> str:
    payload = {
        "graph_id": graph_id,
        "format": fmt,
        "path": str(file_path.resolve()),
        "exp": int(time.time()) + settings.url_ttl_seconds,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    sig = hmac.new(settings.url_secret.encode("utf-8"), raw, hashlib.sha256).digest()
    return _b64(raw) + "." + _b64(sig)


def verify_artifact(token: str) -> dict[str, Any]:
    try:
        raw_b64, sig_b64 = token.split(".", 1)
        raw = _unb64(raw_b64)
        supplied_sig = _unb64(sig_b64)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid artifact token") from exc
    expected_sig = hmac.new(settings.url_secret.encode("utf-8"), raw, hashlib.sha256).digest()
    if not hmac.compare_digest(supplied_sig, expected_sig):
        raise HTTPException(status_code=403, detail="Invalid artifact signature")
    payload = json.loads(raw.decode("utf-8"))
    if int(payload.get("exp", 0)) < int(time.time()):
        raise HTTPException(status_code=410, detail="Artifact token expired")
    path = Path(payload["path"]).resolve()
    artifact_root = settings.artifact_dir.resolve()
    if artifact_root not in path.parents and path != artifact_root:
        raise HTTPException(status_code=403, detail="Artifact path outside store")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Artifact not found")
    payload["path"] = str(path)
    return payload
