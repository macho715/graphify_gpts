from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    service_name: str = os.getenv("GRAPHIFY_SERVICE_NAME", "Graphify GPTS Backend")
    data_dir: Path = Path(os.getenv("GRAPHIFY_DATA_DIR", "./data")).resolve()
    work_dir: Path = Path(os.getenv("GRAPHIFY_WORK_DIR", "./data/workspaces")).resolve()
    graph_dir: Path = Path(os.getenv("GRAPHIFY_GRAPH_DIR", "./data/graphs")).resolve()
    artifact_dir: Path = Path(os.getenv("GRAPHIFY_ARTIFACT_DIR", "./data/artifacts")).resolve()
    audit_log: Path = Path(os.getenv("GRAPHIFY_AUDIT_LOG", "./data/audit.jsonl")).resolve()
    auth_mode: str = os.getenv("GRAPHIFY_AUTH_MODE", "none").lower().strip()
    action_token: str = os.getenv("GRAPHIFY_ACTION_TOKEN", "")
    url_secret: str = os.getenv("GRAPHIFY_URL_SECRET", "dev-url-secret-change-me")
    url_ttl_seconds: int = int(os.getenv("GRAPHIFY_URL_TTL_SECONDS", "900"))
    allowed_hosts: tuple[str, ...] = tuple(
        h.strip().lower()
        for h in os.getenv(
            "GRAPHIFY_ALLOWED_HOSTS",
            "github.com,codeload.github.com,raw.githubusercontent.com,objects.githubusercontent.com",
        ).split(",")
        if h.strip()
    )
    allow_local_path: bool = os.getenv("GRAPHIFY_ALLOW_LOCAL_PATH", "false").lower() in {"1", "true", "yes"}
    max_files: int = int(os.getenv("GRAPHIFY_MAX_FILES", "5000"))
    max_file_bytes: int = int(os.getenv("GRAPHIFY_MAX_FILE_BYTES", "1048576"))
    max_total_bytes: int = int(os.getenv("GRAPHIFY_MAX_TOTAL_BYTES", "104857600"))
    job_workers: int = int(os.getenv("GRAPHIFY_JOB_WORKERS", "2"))
    clone_timeout_seconds: int = int(os.getenv("GRAPHIFY_CLONE_TIMEOUT_SECONDS", "180"))
    run_mode: str = os.getenv("GRAPHIFY_RUN_MODE", "worker").lower().strip()

    def ensure_dirs(self) -> None:
        for path in [self.data_dir, self.work_dir, self.graph_dir, self.artifact_dir, self.audit_log.parent]:
            path.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
