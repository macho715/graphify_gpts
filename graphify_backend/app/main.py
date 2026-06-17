"""FastAPI app entry point."""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from . import audit
from .config import get_settings
from .jobs import restore_once
from .routes.graphs import artifacts_router, router as graphs_router
from .routes.jobs import router as jobs_router


def create_app() -> FastAPI:
    settings = get_settings()
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    restore_once()

    app = FastAPI(
        title="Graphify GPTS Backend",
        version="1.0.0",
        description=(
            "Backend that wraps the `graphify` CLI behind a Bearer-authenticated "
            "HTTP API consumable by a Custom GPT Action."
        ),
    )

    @app.get("/health", tags=["meta"])
    async def health() -> JSONResponse:
        return JSONResponse(
            {
                "status": "ok",
                "version": "1.0.0",
                "allowed_hosts": sorted(settings.allowed_hosts),
            }
        )

    @app.get("/", tags=["meta"])
    async def root() -> JSONResponse:
        return JSONResponse(
            {
                "service": "graphify-gpts-backend",
                "docs": "/docs",
                "openapi": "/openapi.json",
            }
        )

    app.include_router(jobs_router)
    app.include_router(graphs_router)
    app.include_router(artifacts_router)

    @app.on_event("startup")
    async def _startup() -> None:
        audit.audit("service.started", allowed_hosts=sorted(settings.allowed_hosts))

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        audit.audit("service.stopped")

    return app


app = create_app()
