from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import httpx


def check(name: str, condition: bool, payload=None) -> dict:
    row = {"test": name, "status": "PASS" if condition else "FAIL"}
    if payload is not None:
        row["payload"] = payload
    if not condition:
        print(json.dumps(row, ensure_ascii=False, indent=2))
        raise AssertionError(name)
    print(f"PASS {name}")
    return row


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--fixture", default=str(Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "tiny_repo"))
    parser.add_argument("--report", default=str(Path(__file__).resolve().parents[2] / "TEST_REPORT.md"))
    parser.add_argument("--graph-id", default="smoke-tiny")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    rows: list[dict] = []
    with httpx.Client(timeout=30.0) as client:
        r = client.get(f"{base}/health")
        rows.append(check("1_health", r.status_code == 200 and r.json().get("status") == "ok", r.json()))

        build_payload = {
            "source": {"type": "local_path", "path": args.fixture},
            "options": {"graph_id": args.graph_id, "synchronous": True, "audit_label": "5x-smoke"},
        }
        r = client.post(f"{base}/v1/graphify/jobs", json=build_payload)
        data = r.json()
        rows.append(check("2_build_local_fixture", r.status_code == 200 and data.get("status") == "succeeded" and data.get("graph_id") == args.graph_id, data))
        graph_id = data["graph_id"]

        r = client.get(f"{base}/v1/graphify/graphs/{graph_id}/stats")
        stats = r.json()
        rows.append(check("3_stats_persistent_graph", r.status_code == 200 and stats.get("nodes", 0) >= 8 and stats.get("files", 0) >= 3, stats))

        r = client.post(f"{base}/v1/graphify/graphs/{graph_id}/query", json={"query": "invoice validate shipment", "limit": 5})
        q = r.json()
        rows.append(check("4_query_returns_hits", r.status_code == 200 and len(q.get("hits", [])) >= 1, q))

        r_path = client.post(f"{base}/v1/graphify/graphs/{graph_id}/path", json={"source": "project:root", "target": "validate_invoice", "max_depth": 6})
        r_exp = client.post(f"{base}/v1/graphify/graphs/{graph_id}/explain", json={"query": "validate_invoice", "depth": 2})
        r_aff = client.post(f"{base}/v1/graphify/graphs/{graph_id}/affected", json={"query": "src/invoice.py", "direction": "both", "max_depth": 2, "limit": 20})
        ok = r_path.status_code == 200 and r_exp.status_code == 200 and r_aff.status_code == 200 and r_exp.json().get("node")
        rows.append(check("5_path_explain_affected", ok, {"path": r_path.json(), "explain": r_exp.json(), "affected_count": len(r_aff.json().get("affected", []))}))

        r = client.post(f"{base}/v1/graphify/graphs/{graph_id}/export", json={"format": "zip"})
        exp = r.json()
        token = exp.get("artifact_token")
        dl = client.get(f"{base}/v1/graphify/artifacts/{token}") if token else None
        rows.append(check("6_export_artifact_download", r.status_code == 200 and dl is not None and dl.status_code == 200 and len(dl.content) > 100, {"export": exp, "bytes": len(dl.content) if dl else 0}))

        update_payload = {
            "source": {"type": "inline_files", "files": [{"path": "README.md", "content": "# Inline Update\n\nGraphify update validates affected nodes."}, {"path": "src/update.py", "content": "def update_graph():\n    return 'ok'\n"}]},
            "options": {"synchronous": True},
        }
        r = client.post(f"{base}/v1/graphify/graphs/{graph_id}/update", json=update_payload)
        up = r.json()
        rows.append(check("7_update_existing_graph_id", r.status_code == 200 and up.get("status") == "succeeded" and up.get("graph_id") == graph_id, up))

    lines = ["# Graphify Backend 5x Test Report", "", f"- Base URL: `{base}`", f"- Fixture: `{args.fixture}`", "", "| No | Test | Status |", "|---:|---|---|"]
    for i, row in enumerate(rows, 1):
        lines.append(f"| {i} | {row['test']} | {row['status']} |")
    lines.append("")
    lines.append("## Raw Results")
    lines.append("```json")
    lines.append(json.dumps(rows, ensure_ascii=False, indent=2))
    lines.append("```")
    Path(args.report).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"WROTE {args.report}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}", file=sys.stderr)
        raise
