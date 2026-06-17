from __future__ import annotations

import mimetypes
import re
from pathlib import Path
from urllib.parse import urlparse

from .config import settings

SENSITIVE_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
    "credentials.json",
    "service-account.json",
    "secrets.json",
    ".npmrc",
    ".pypirc",
    ".netrc",
}
SENSITIVE_PARTS = {".git", ".ssh", ".aws", ".gcp", ".azure", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", ".next", ".turbo"}
TEXT_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".go", ".rs", ".java", ".kt",
    ".cs", ".cpp", ".c", ".h", ".hpp", ".rb", ".php", ".swift", ".scala", ".lua",
    ".sh", ".bash", ".ps1", ".sql", ".tf", ".hcl", ".yaml", ".yml", ".json", ".toml",
    ".ini", ".cfg", ".md", ".mdx", ".txt", ".rst", ".html", ".css", ".scss", ".xml",
    ".csv", ".dockerfile", "", ".gitignore", ".dockerignore",
}
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".tar", ".gz", ".7z", ".rar",
    ".exe", ".dll", ".so", ".dylib", ".class", ".jar", ".mp4", ".mov", ".mp3", ".wav", ".xlsx", ".docx",
}
SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|token|secret|password|passwd|pwd)\s*[:=]\s*['\"]?[^'\"\s,;]{8,}"),
    re.compile(r"(?i)Bearer\s+[A-Za-z0-9._~+\-/=]{16,}"),
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
]


def validate_public_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"https"}:
        raise ValueError("Only https URLs are allowed")
    host = (parsed.hostname or "").lower()
    if host not in settings.allowed_hosts:
        raise ValueError(f"Host not allowed: {host}")
    if host in {"localhost", "127.0.0.1", "0.0.0.0"}:
        raise ValueError("Localhost URLs are blocked")
    return host


def should_skip(path: Path, root: Path) -> tuple[bool, str | None]:
    try:
        rel = path.relative_to(root)
    except ValueError:
        rel = path
    parts = {p.lower() for p in rel.parts}
    if any(part in SENSITIVE_PARTS for part in parts):
        return True, "sensitive_or_generated_path"
    if path.name.lower() in SENSITIVE_NAMES:
        return True, "sensitive_filename"
    suffix = path.suffix.lower()
    if suffix in BINARY_EXTENSIONS:
        return True, "binary_extension"
    if suffix not in TEXT_EXTENSIONS and not is_probably_text(path):
        return True, "non_text"
    try:
        if path.stat().st_size > settings.max_file_bytes:
            return True, "file_too_large"
    except OSError:
        return True, "stat_failed"
    return False, None


def is_probably_text(path: Path) -> bool:
    guess = mimetypes.guess_type(str(path))[0]
    if guess and guess.startswith("text/"):
        return True
    return path.suffix.lower() in TEXT_EXTENSIONS or path.name.lower() in {"dockerfile", "makefile", "license", "readme"}


def redact_inline_secrets(text: str) -> tuple[str, int]:
    count = 0
    out = text
    for pattern in SECRET_PATTERNS:
        out, n = pattern.subn("[REDACTED]", out)
        count += n
    return out, count
