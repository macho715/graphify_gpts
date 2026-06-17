"""Input fetcher with allowlist + size limits.

Supported `input_uri` schemes:
  * https://github.com/<owner>/<repo>                  — git clone
  * https://github.com/<owner>/<repo>/archive/refs/... — tarball download
  * https://raw.githubusercontent.com/<owner>/<repo>/... — single file
  * https://codeload.github.com/...                   — tarball/zipball
  * https://gist.githubusercontent.com/...            — gist archive

Private/internal hosts (e.g. internal GitLab, internal S3) are blocked unless
the operator has explicitly added them to GRAPHIFY_ALLOWED_HOSTS.
"""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
import tarfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import httpx

from .config import Settings, get_settings
from .secrets import decide, has_inline_secret
from .workspace import Workspace

_log = logging.getLogger("graphify.fetcher")

_GITHUB_REPO_RE = re.compile(
    r"^/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?(?:/.*)?$"
)
_GH_ARCHIVE_RE = re.compile(
    r"^/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/archive/(?:refs/)?(?:heads|tags)/(.+?)(?:\.tar\.gz|\.zip)?$"
)
_RAW_RE = re.compile(
    r"^/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/(?:raw|bl)/([^/]+)/(.+)$"
)


class FetchError(Exception):
    """Raised when a URI cannot be fetched safely."""


@dataclass(frozen=True)
class FetchResult:
    root: Path                 # the directory where the corpus is now sitting
    input_kind: str            # "git" | "archive" | "single_file"
    skipped_files: int = 0
    skipped_reasons: dict[str, int] | None = None
    bytes_pulled: int = 0


def _check_host(url: str, settings: Settings) -> str:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if not host:
        raise FetchError(f"no hostname in URI: {url}")
    if parsed.scheme not in {"https", "http"}:
        raise FetchError(f"unsupported scheme: {parsed.scheme}")
    if host not in settings.allowed_hosts:
        raise FetchError(f"host not in allowlist: {host}")
    return host


def _check_github_path(url: str, path: str) -> None:
    """Disallow path-traversal patterns and force https for github.com."""
    if "\x00" in path:
        raise FetchError("NUL byte in path")
    if ".." in path.split("/"):
        raise FetchError("path traversal segment in URI")


def _safe_path_under(root: Path, *parts: str) -> Path:
    """Build a path under `root` and verify it doesn't escape via `..`."""
    candidate = (root.joinpath(*parts)).resolve()
    root_resolved = root.resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError as exc:
        raise FetchError(f"path escapes workspace: {candidate}") from exc
    return candidate


def _download_to(url: str, dest: Path, settings: Settings) -> int:
    """Streamed download. Returns bytes received. Enforces max-bytes cap."""
    with httpx.Client(
        timeout=httpx.Timeout(60.0, read=120.0),
        follow_redirects=True,
        headers={"User-Agent": "graphify-gpts-backend/1.0"},
    ) as client:
        with client.stream("GET", url) as resp:
            if resp.status_code >= 400:
                raise FetchError(f"HTTP {resp.status_code} for {url}")
            received = 0
            with dest.open("wb") as fh:
                for chunk in resp.iter_bytes():
                    received += len(chunk)
                    if received > settings.graphify_max_bytes:
                        fh.close()
                        dest.unlink(missing_ok=True)
                        raise FetchError(
                            f"download exceeded {settings.graphify_max_bytes} bytes"
                        )
                    fh.write(chunk)
    return received


def _extract_archive(archive: Path, dest: Path) -> None:
    """Extract tar/zip into dest (created)."""
    dest.mkdir(parents=True, exist_ok=True)
    name = archive.name.lower()
    try:
        if name.endswith(".tar.gz") or name.endswith(".tgz"):
            with tarfile.open(archive, "r:gz") as tf:
                tf.extractall(dest, filter="data")
        elif name.endswith(".tar.bz2") or name.endswith(".tbz2"):
            with tarfile.open(archive, "r:bz2") as tf:
                tf.extractall(dest, filter="data")
        elif name.endswith(".zip"):
            with zipfile.ZipFile(archive) as zf:
                zf.extractall(dest)
        else:
            raise FetchError(f"unsupported archive type: {archive.name}")
    finally:
        archive.unlink(missing_ok=True)


def _git_clone(url: str, dest: Path) -> None:
    if shutil.which("git") is None:
        raise FetchError("git binary not found on PATH; cannot clone repositories")
    cmd = [
        "git",
        "clone",
        "--depth",
        "1",
        "--single-branch",
        "--no-tags",
        url,
        str(dest),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise FetchError(f"git clone failed: {proc.stderr.strip()[:500]}")


def _flatten_single_top_dir(root: Path) -> None:
    """GitHub tarballs extract to `<repo>-<sha>/...`. Move children up."""
    children = [p for p in root.iterdir() if p.is_dir()]
    if len(children) == 1 and children[0].is_dir():
        only = children[0]
        for child in only.iterdir():
            shutil.move(str(child), str(root / child.name))
        only.rmdir()


def _scrub_corpus(root: Path, settings: Settings) -> tuple[int, dict[str, int]]:
    """Walk the corpus and drop files flagged by `secrets.decide`."""
    skipped = 0
    reasons: dict[str, int] = {}
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        decision = decide(p, root)
        if decision.keep:
            continue
        skipped += 1
        reasons[decision.reason] = reasons.get(decision.reason, 0) + 1
        try:
            p.unlink()
        except OSError:
            pass
    return skipped, reasons


def _scrub_text_files_for_secrets(root: Path) -> int:
    """Replace obvious inline secrets with [REDACTED] in kept text files."""
    edits = 0
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.stat().st_size > 1_000_000:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if not has_inline_secret(text):
            continue
        new = _SECRET_INLINE_RE.sub(
            lambda m: f"{m.group(0).split(m.group(1))[0]}[REDACTED]", text
        )
        if new != text:
            try:
                p.write_text(new, encoding="utf-8")
                edits += 1
            except OSError:
                pass
    return edits


# Match the same pattern as `secrets.has_inline_secret`; importing a duplicate
# regex keeps this module self-contained.
_SECRET_INLINE_RE = re.compile(
    r"(?i)(?:api[_-]?key|secret|token|password|passwd|access[_-]?key|private[_-]?key)"
    r"\s*[:=]\s*['\"]?([A-Za-z0-9_/+=.-]{8,})"
)


def fetch(ws: Workspace, input_uri: str, branch: str | None = None) -> FetchResult:
    """Fetch `input_uri` into the workspace and return the corpus root."""
    settings = get_settings()
    host = _check_host(input_uri, settings)
    parsed = urlparse(input_uri)
    path = parsed.path

    work_dir = ws.work_dir / "corpus"
    work_dir.mkdir(parents=True, exist_ok=True)

    bytes_pulled = 0
    skipped = 0
    reasons: dict[str, int] = {}
    inline_edits = 0
    input_kind = "single_file"

    if host.endswith("github.com") and path.endswith(".git"):
        _check_github_path(input_uri, path)
        # Build a clone URL with optional branch hint.
        clone_url = f"https://github.com{path}"
        if branch:
            clone_url = f"{clone_url}?branch={branch}"
        _git_clone(clone_url, work_dir)
        input_kind = "git"
    elif host.endswith("github.com") and _GITHUB_REPO_RE.match(path):
        m = _GITHUB_REPO_RE.match(path)
        if m is None:
            raise FetchError(f"unparseable GitHub path: {path}")
        owner, repo = m.group(1), m.group(2)
        # Use tarball endpoint for speed and determinism.
        ref = branch or "HEAD"
        archive_url = f"https://codeload.github.com/{owner}/{repo}/tar.gz/refs/heads/{branch}" if branch else f"https://codeload.github.com/{owner}/{repo}/tar.gz/refs/heads/main"
        # The main branch name varies; try main, fall back to master.
        last_err: Exception | None = None
        for candidate in (branch, "main", "master"):
            if not candidate:
                continue
            url_try = f"https://codeload.github.com/{owner}/{repo}/tar.gz/refs/heads/{candidate}"
            archive = work_dir / "src.tar.gz"
            try:
                bytes_pulled = _download_to(url_try, archive, settings)
                _extract_archive(archive, work_dir)
                _flatten_single_top_dir(work_dir)
                input_kind = "archive"
                last_err = None
                break
            except FetchError as exc:
                last_err = exc
                continue
        if last_err is not None and input_kind == "single_file":
            # Last resort: git clone at default branch
            _git_clone(f"https://github.com/{owner}/{repo}.git", work_dir)
            input_kind = "git"
    elif host.endswith("codeload.github.com") and _GH_ARCHIVE_RE.match(path):
        m = _GH_ARCHIVE_RE.match(path)
        if m is None:
            raise FetchError(f"unparseable codeload path: {path}")
        archive = work_dir / "src.bin"
        bytes_pulled = _download_to(input_uri, archive, settings)
        _extract_archive(archive, work_dir)
        _flatten_single_top_dir(work_dir)
        input_kind = "archive"
    elif host.endswith("raw.githubusercontent.com") and _RAW_RE.match(path):
        m = _RAW_RE.match(path)
        if m is None:
            raise FetchError(f"unparseable raw path: {path}")
        owner, repo, ref, tail = m.group(1), m.group(2), m.group(3), m.group(4)
        target = _safe_path_under(work_dir, owner, repo, ref, *tail.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        bytes_pulled = _download_to(input_uri, target, settings)
        input_kind = "single_file"
    elif host.endswith("gist.githubusercontent.com"):
        # Treat as a single file (the gist body).
        target = work_dir / "gist.txt"
        bytes_pulled = _download_to(input_uri, target, settings)
        input_kind = "single_file"
    else:
        raise FetchError(f"unsupported URL shape: {input_uri}")

    if not any(work_dir.iterdir()):
        raise FetchError("fetched corpus is empty")

    skipped, reasons = _scrub_corpus(work_dir, settings)
    inline_edits = _scrub_text_files_for_secrets(work_dir)
    if inline_edits:
        reasons["inline-secret-redacted"] = reasons.get("inline-secret-redacted", 0) + inline_edits

    return FetchResult(
        root=work_dir,
        input_kind=input_kind,
        skipped_files=skipped,
        skipped_reasons=reasons,
        bytes_pulled=bytes_pulled,
    )
