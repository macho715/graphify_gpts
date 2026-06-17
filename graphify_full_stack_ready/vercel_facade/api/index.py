from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import Response

BACKEND_URL = os.getenv("GRAPHIFY_BACKEND_URL", "").rstrip("/")
BACKEND_TOKEN = os.getenv("GRAPHIFY_BACKEND_TOKEN", "")
FACADE_TOKEN = os.getenv("GRAPHIFY_FACADE_TOKEN", "")

app = FastAPI(title="Graphify Vercel Facade", version="1.0.0")


def check_facade_auth(authorization: str | None) -> None:
    if not FACADE_TOKEN:
        return
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing facade bearer token")
    if authorization.split(" ", 1)[1].strip() != FACADE_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid facade bearer token")


@app.get("/")
async def root():
    return {"service": "graphify-vercel-facade", "backend_configured": bool(BACKEND_URL)}


@app.get("/health", operation_id="graphifyHealth")
async def health(authorization: str | None = Header(default=None)):
    check_facade_auth(authorization)
    if not BACKEND_URL:
        return {"status": "facade_only", "backend_configured": False}
    headers = {"Authorization": f"Bearer {BACKEND_TOKEN}"} if BACKEND_TOKEN else {}
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(f"{BACKEND_URL}/health", headers=headers)
    return Response(content=r.content, status_code=r.status_code, media_type=r.headers.get("content-type", "application/json"))


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"], operation_id="graphifyProxy")
async def proxy(path: str, request: Request, authorization: str | None = Header(default=None)):
    check_facade_auth(authorization)
    if not BACKEND_URL:
        raise HTTPException(status_code=503, detail="GRAPHIFY_BACKEND_URL is not configured")
    url = f"{BACKEND_URL}/{path}"
    headers = {k: v for k, v in request.headers.items() if k.lower() not in {"host", "authorization", "content-length"}}
    if BACKEND_TOKEN:
        headers["Authorization"] = f"Bearer {BACKEND_TOKEN}"
    body = await request.body()
    async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
        r = await client.request(request.method, url, params=request.query_params, content=body, headers=headers)
    passthrough_headers = {k: v for k, v in r.headers.items() if k.lower() in {"content-type", "content-disposition", "cache-control"}}
    return Response(content=r.content, status_code=r.status_code, headers=passthrough_headers, media_type=r.headers.get("content-type"))
