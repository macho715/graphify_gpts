"""Bearer-token auth.

- `verify_bearer(authorization_header, settings) -> str` returns the matched key
  or raises HTTP 401.
- Keys are stored hashed in memory so a process dump does not leak raw keys;
  we use a constant-time compare on a SHA-256 prefix to avoid timing oracles.
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Final

from fastapi import Header, HTTPException, status

from .config import Settings, get_settings

_SCHEME: Final = "bearer "


def _hash(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def verify_bearer(authorization: str | None, settings: Settings) -> str:
    """Return the matched API key on success, otherwise raise 401."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not authorization.lower().startswith(_SCHEME):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization scheme must be Bearer",
            headers={"WWW-Authenticate": "Bearer"},
        )
    presented = authorization[len(_SCHEME) :].strip()
    if not presented:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Empty bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    presented_h = _hash(presented)
    for raw in settings.api_key_set:
        if hmac.compare_digest(presented_h, _hash(raw)):
            return raw
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def require_bearer(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> str:
    """FastAPI dependency."""
    return verify_bearer(authorization, get_settings())


async def require_admin(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> str:
    """Admin key dependency for destructive operations."""
    s = get_settings()
    if not s.graphify_admin_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin key not configured",
        )
    if not authorization or not authorization.lower().startswith(_SCHEME):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or non-Bearer Authorization",
            headers={"WWW-Authenticate": "Bearer"},
        )
    presented = authorization[len(_SCHEME) :].strip()
    if not hmac.compare_digest(presented, s.graphify_admin_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return presented
