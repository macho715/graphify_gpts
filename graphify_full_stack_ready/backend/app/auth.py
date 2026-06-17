from __future__ import annotations

import hashlib
import hmac

from fastapi import Header, HTTPException, status

from .config import settings


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def require_auth(authorization: str | None = Header(default=None)) -> None:
    mode = settings.auth_mode
    if mode in {"", "none", "off", "disabled"}:
        return
    if mode != "bearer":
        raise HTTPException(status_code=500, detail=f"Unsupported GRAPHIFY_AUTH_MODE={mode}")
    if not settings.action_token:
        raise HTTPException(status_code=500, detail="GRAPHIFY_ACTION_TOKEN is required when auth_mode=bearer")
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    supplied = authorization.split(" ", 1)[1].strip()
    if not hmac.compare_digest(_sha256(supplied), _sha256(settings.action_token)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid bearer token")
