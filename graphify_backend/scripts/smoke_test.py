"""End-to-end smoke test that exercises every endpoint in the OpenAPI schema.

Usage:
    python scripts/smoke_test.py --base http://127.0.0.1:8765 --key dev-smoke-key
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any

import httpx

# A tiny public repo that builds fast and has known nodes/edges.
DEFAULT_REPO = "https://github.com/octocat/Spoon-Knife"


def _check(condition: bool, label: str, details: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    line = f"[{status}] {label}"
    if details:
        line += f" — {details}"
    print(line, flush=True)
    if not condition:
        raise SystemExit(1)


def _poll_job(client: httpx.Client, base: str, key: str, job_id: str, timeout_s: int = 300) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        r = client.get(
            f"{base}/v1/graphify/jobs/{job_id}",
            headers={"Authorization": f"Bearer {key}"},
        )
        if r.status_code != 200:
            _check(False, f"job poll status={r.status_code}", r.text[:200])
        job = r.json()
        if job["status"] in {"succeeded", "failed", "cancelled"}:
            return job
        time.sleep(1.0)
    _check(False, f"job {job_id} did not finish within {timeout_s}s")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--base", required=True)
    p.add_argument("--key", required=True)
    p.add_argument("--repo", default=DEFAULT_REPO)
    args = p.parse_args()

    base = args.base.rstrip("/")
    key = args.key
    repo = args.repo

    with httpx.Client(timeout=30) as client:
        # --- Health ---
        r = client.get(f"{base}/health")
        _check(r.status_code == 200, "GET /health", r.text[:120])

        # --- Auth: missing key ---
        r = client.post(f"{base}/v1/graphify/jobs", json={"input_uri": repo})
        _check(r.status_code == 401, "POST /jobs without key returns 401", str(r.status_code))

        # --- Auth: bad key ---
        r = client.post(
            f"{base}/v1/graphify/jobs",
            json={"input_uri": repo},
            headers={"Authorization": "Bearer not-the-right-key"},
        )
        _check(r.status_code == 401, "POST /jobs with bad key returns 401", str(r.status_code))

        # --- Fetcher allowlist: github.com only ---
        r = client.post(
            f"{base}/v1/graphify/jobs",
            json={"input_uri": "https://example.com/foo.git"},
            headers={"Authorization": f"Bearer {key}"},
        )
        # Build is async — allowlist check happens in the worker. We kick it off
        # then poll to make sure it fails fast.
        if r.status_code == 200:
            job = r.json()
            final = _poll_job(client, base, key, job["job_id"], timeout_s=20)
            _check(final["status"] == "failed", "blocked-host job fails", final.get("message", "")[:120])
        else:
            _check(r.status_code in (200, 400, 422), "blocked host accepted/rejected appropriately", str(r.status_code))

        # --- Build a real repo ---
        print(f"[smoke] building {repo}", flush=True)
        r = client.post(
            f"{base}/v1/graphify/jobs",
            json={"input_uri": repo, "mode": "standard", "no_viz": True},
            headers={"Authorization": f"Bearer {key}"},
        )
        _check(r.status_code == 200, "POST /jobs build", str(r.status_code))
        job = r.json()
        final = _poll_job(client, base, key, job["job_id"], timeout_s=240)
        _check(final["status"] == "succeeded", "build job succeeded", final.get("message", "")[:200])
        graph_id = final["graph_id"]
        _check(bool(graph_id), "build returns graph_id", graph_id)

        # --- Stats ---
        r = client.get(
            f"{base}/v1/graphify/graphs/{graph_id}/stats",
            headers={"Authorization": f"Bearer {key}"},
        )
        _check(r.status_code == 200, "GET /stats", "")
        s = r.json()
        _check(s["nodes"] > 0, "stats.nodes > 0", str(s["nodes"]))
        _check(s["edges"] > 0, "stats.edges > 0", str(s["edges"]))

        # --- Query ---
        r = client.post(
            f"{base}/v1/graphify/graphs/{graph_id}/query",
            json={"question": "what does the README describe", "mode": "bfs", "token_budget": 1500},
            headers={"Authorization": f"Bearer {key}"},
        )
        _check(r.status_code == 200, "POST /query", "")
        q = r.json()
        _check(bool(q.get("result")), "query.result is non-empty", q.get("result", "")[:80])

        # --- Query with context_filter (verifies spec field is wired through) ---
        r = client.post(
            f"{base}/v1/graphify/graphs/{graph_id}/query",
            json={
                "question": "README",
                "mode": "bfs",
                "token_budget": 1500,
                "context_filter": ["contains"],
            },
            headers={"Authorization": f"Bearer {key}"},
        )
        _check(r.status_code == 200, "POST /query with context_filter", "")
        qf = r.json()
        _check(bool(qf.get("result")), "context_filter query returns a result", qf.get("result", "")[:80])

        # --- Path ---
        r = client.post(
            f"{base}/v1/graphify/graphs/{graph_id}/path",
            json={"source": "README", "target": "contributor"},
            headers={"Authorization": f"Bearer {key}"},
        )
        _check(r.status_code == 200, "POST /path", r.text[:200])

        # --- Explain ---
        r = client.post(
            f"{base}/v1/graphify/graphs/{graph_id}/explain",
            json={"label": "README", "depth": 2},
            headers={"Authorization": f"Bearer {key}"},
        )
        _check(r.status_code == 200, "POST /explain", "")

        # --- Affected ---
        r = client.post(
            f"{base}/v1/graphify/graphs/{graph_id}/affected",
            json={"label": "README", "depth": 2},
            headers={"Authorization": f"Bearer {key}"},
        )
        _check(r.status_code == 200, "POST /affected", "")

        # --- Export JSON ---
        r = client.post(
            f"{base}/v1/graphify/graphs/{graph_id}/export",
            json={"format": "json"},
            headers={"Authorization": f"Bearer {key}"},
        )
        _check(r.status_code == 200, "POST /export json", "")
        exp = r.json()
        _check(bool(exp.get("download_url")), "export returns download_url", exp.get("download_url", "")[:120])

        # --- Download via signed URL ---
        url = exp["download_url"]
        # The signed URL points to a different host (whatever base_url was).
        # For local smoke tests, point it back at our base.
        if url.startswith("http://") or url.startswith("https://"):
            download = client.get(url)
        else:
            download = client.get(f"{base}{url}")
        _check(download.status_code == 200, "signed-url download succeeds", f"status={download.status_code}")

        # --- Export graphml (also exercises the renderer) ---
        r = client.post(
            f"{base}/v1/graphify/graphs/{graph_id}/export",
            json={"format": "graphml"},
            headers={"Authorization": f"Bearer {key}"},
        )
        _check(r.status_code == 200, "POST /export graphml", "")

        # --- Unknown graph ---
        r = client.get(
            f"{base}/v1/graphify/graphs/does-not-exist/stats",
            headers={"Authorization": f"Bearer {key}"},
        )
        _check(r.status_code == 404, "GET /stats unknown graph returns 404", str(r.status_code))

    print("[smoke] all checks passed", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
