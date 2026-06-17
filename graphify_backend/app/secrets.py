"""Secrets / PII scanning for fetched files.

Decides whether a file should be skipped or redacted before graph extraction.
The `graphify` CLI does not skip files itself; we drop them at the workspace
level so they never enter the corpus.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# File names that almost always contain credentials. We do not extract graph
# nodes from them and we also drop them from the corpus to prevent accidental
# inclusion in GRAPH_REPORT.md or graph.json summaries.
_SENSITIVE_NAMES: tuple[str, ...] = (
    ".env",
    ".env.local",
    ".env.production",
    "id_rsa",
    "id_ed25519",
    "id_dsa",
    "id_ecdsa",
    "credentials.json",
    "service-account.json",
    "service_account.json",
    "gha-creds.json",
    ".npmrc",
    ".pypirc",
    ".netrc",
    "secrets.yaml",
    "secrets.yml",
    "htpasswd",
    "shadow",
)

# Path substrings we never want to import.
_SENSITIVE_PATH_HINTS: tuple[str, ...] = (
    "/.ssh/",
    "/.aws/",
    "/.gcp/",
    "/.kube/",
    "/.docker/",
    "/secrets/",
    "/credentials/",
    "/.gnupg/",
    "/.config/gh/",
)

# Directories we skip wholesale.
_SKIP_DIRS: tuple[str, ...] = (
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".next",
    ".nuxt",
    "dist",
    "build",
    "target",  # rust
    ".gradle",
    ".idea",
    ".vscode",
    "graphify-out",  # never recurse into a previous build
    "var",  # our own working dir
)

# Hard byte cap. Anything larger is treated as binary and skipped.
_MAX_FILE_BYTES = 5_000_000  # 5 MB

# If the file is "high entropy", treat as binary.
_BINARY_SNIFF_BYTES = 8192
_NULL_BYTE_THRESHOLD = 0.01  # >1% null bytes => binary


@dataclass(frozen=True)
class FileDecision:
    path: Path
    keep: bool
    reason: str


def _looks_binary(head: bytes) -> bool:
    if not head:
        return False
    if b"\x00" in head:
        # Heuristic: any NUL byte in the first 8K.
        null_ratio = head.count(b"\x00") / len(head)
        return null_ratio > _NULL_BYTE_THRESHOLD
    try:
        head.decode("utf-8")
        return False
    except UnicodeDecodeError:
        return True


def decide(path: Path, root: Path) -> FileDecision:
    """Return keep/skip decision for a single file under `root`."""
    rel = path.relative_to(root)
    rel_str = str(rel).replace("\\", "/")
    name = path.name

    # Directory check
    for skip in _SKIP_DIRS:
        if skip in rel.parts:
            return FileDecision(path, keep=False, reason=f"dir:{skip}")

    # Sensitive name
    if name in _SENSITIVE_NAMES:
        return FileDecision(path, keep=False, reason="sensitive-name")

    # Sensitive path hint
    for hint in _SENSITIVE_PATH_HINTS:
        if hint in f"/{rel_str}":
            return FileDecision(path, keep=False, reason="sensitive-path")

    # Size cap
    try:
        size = path.stat().st_size
    except OSError:
        return FileDecision(path, keep=False, reason="stat-error")
    if size > _MAX_FILE_BYTES:
        return FileDecision(path, keep=False, reason="oversize")

    # Binary sniff
    try:
        with path.open("rb") as fh:
            head = fh.read(_BINARY_SNIFF_BYTES)
    except OSError:
        return FileDecision(path, keep=False, reason="read-error")
    if _looks_binary(head):
        return FileDecision(path, keep=False, reason="binary")

    return FileDecision(path, keep=True, reason="ok")


_SECRET_INLINE = re.compile(
    r"(?i)(?:api[_-]?key|secret|token|password|passwd|access[_-]?key|private[_-]?key)"
    r"\s*[:=]\s*['\"]?([A-Za-z0-9_/+=.-]{8,})"
)


def has_inline_secret(text: str) -> bool:
    """Conservative check: does the text contain an obvious inline secret?"""
    return bool(_SECRET_INLINE.search(text))
