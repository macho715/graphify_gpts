"""Configuration loaded from environment variables.

All deployment-relevant settings come from env so secrets never live in code.
See .env.example for the full list.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Server settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- Auth ----
    graphify_api_keys: str = Field(
        default="dev-key-1",
        description="Comma-separated Bearer API keys accepted by the service.",
    )
    graphify_admin_key: str | None = Field(
        default=None,
        description="Master key for /admin endpoints (deletion, stats, etc).",
    )

    # ---- Storage ----
    graphify_work_root: Path = Field(
        default=Path("./var/workspaces"),
        description="Per-job workspace root. Each job gets a subdirectory.",
    )
    graphify_artifact_root: Path = Field(
        default=Path("./var/artifacts"),
        description="Artifact (graph.json, GRAPH_REPORT.md, graph.html) root.",
    )
    graphify_audit_log: Path = Field(
        default=Path("./var/audit.log"),
        description="JSONL audit log path.",
    )

    # ---- Signed URLs ----
    graphify_url_secret: str = Field(
        default="change-me-to-a-long-random-string-at-least-32-chars",
        min_length=32,
        description="HMAC secret for signed artifact download URLs.",
    )
    graphify_url_ttl_seconds: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="Validity of a signed artifact download URL in seconds.",
    )

    # ---- Fetcher allowlist ----
    graphify_allowed_hosts: str = Field(
        default="github.com,raw.githubusercontent.com,codeload.github.com",
        description="Comma-separated hostnames the fetcher will accept.",
    )

    # ---- Build constraints ----
    graphify_max_build_seconds: int = Field(default=900, ge=30, le=7200)
    graphify_max_files: int = Field(default=20_000, ge=100)
    graphify_max_bytes: int = Field(default=500_000_000, ge=1_000_000)

    # ---- CLI ----
    graphify_cli_bin: str = Field(default="graphify")

    # ---- Derived helpers ----
    @field_validator("graphify_work_root", "graphify_artifact_root", "graphify_audit_log")
    @classmethod
    def _coerce_to_path(cls, v: object) -> Path:
        return Path(v) if not isinstance(v, Path) else v

    @property
    def api_key_set(self) -> set[str]:
        return {k.strip() for k in self.graphify_api_keys.split(",") if k.strip()}

    @property
    def allowed_hosts(self) -> set[str]:
        return {h.strip().lower() for h in self.graphify_allowed_hosts.split(",") if h.strip()}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings instance."""
    s = Settings()
    s.graphify_work_root.mkdir(parents=True, exist_ok=True)
    s.graphify_artifact_root.mkdir(parents=True, exist_ok=True)
    s.graphify_audit_log.parent.mkdir(parents=True, exist_ok=True)
    return s
