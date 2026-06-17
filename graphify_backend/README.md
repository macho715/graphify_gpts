# Graphify GPTS Backend

Backend service that wraps the [`graphify`](https://github.com/) CLI behind a
Bearer-authenticated HTTP API consumable by a Custom GPT Action.

Implements the contract defined in
[`04_BACKEND_IMPLEMENTATION_PLAN.md`](../graphify_gpts_pack/04_BACKEND_IMPLEMENTATION_PLAN.md)
and exposes every operation in
[`03_OPENAPI_ACTION_SCHEMA.yaml`](../graphify_gpts_pack/03_OPENAPI_ACTION_SCHEMA.yaml).

## Endpoints

| Method | Path | operationId |
|---|---|---|
| `POST` | `/v1/graphify/jobs` | `graphifyBuild` |
| `GET`  | `/v1/graphify/jobs/{job_id}` | `graphifyJobStatus` |
| `DELETE` | `/v1/graphify/jobs/{job_id}` | `graphifyJobCancel` |
| `POST` | `/v1/graphify/graphs/{graph_id}/update` | `graphifyUpdate` |
| `GET`  | `/v1/graphify/graphs/{graph_id}/stats` | `graphifyStats` |
| `POST` | `/v1/graphify/graphs/{graph_id}/query` | `graphifyQuery` |
| `POST` | `/v1/graphify/graphs/{graph_id}/path` | `graphifyPath` |
| `POST` | `/v1/graphify/graphs/{graph_id}/explain` | `graphifyExplain` |
| `POST` | `/v1/graphify/graphs/{graph_id}/affected` | `graphifyAffected` |
| `POST` | `/v1/graphify/graphs/{graph_id}/export` | `graphifyExport` |
| `GET`  | `/v1/graphify/artifacts/{token}` | `graphifyArtifactDownload` |

## Quick start

```bash
cd graphify_backend
cp .env.example .env
# Edit GRAPHIFY_API_KEYS and GRAPHIFY_URL_SECRET

pip install -r requirements.txt
bash scripts/start_dev.sh          # http://localhost:8000
```

Browse the OpenAPI UI at `http://localhost:8000/docs`.

## Smoke test

```bash
bash scripts/run_tests.sh
```

The script:
1. Boots uvicorn on a free port.
2. Runs `scripts/smoke_test.py` which exercises every endpoint against the
   public [`octocat/Hello-World`](https://github.com/octocat/Hello-World) repo.
3. Tears the server down.

## Architecture

```
graphify_backend/
├── app/
│   ├── auth.py            Bearer API key + admin key (HMAC constant-time)
│   ├── audit.py           JSONL audit log, secret/PII redaction
│   ├── config.py          Pydantic-settings; env-only
│   ├── fetcher.py         URL allowlist; git clone / tarball / single file
│   ├── graphify_runner.py subprocess wrapper for the `graphify` CLI
│   ├── jobs.py            In-memory job store + thread pool + JSONL snapshot
│   ├── models.py          Pydantic schemas (mirror the OpenAPI action schema)
│   ├── query_service.py   query / path / explain / affected envelopes
│   ├── secrets.py         File decision (skip / keep) + inline-secret scan
│   ├── workspace.py       Per-job temp workspace
│   ├── artifacts.py       Artifact store + HMAC-signed download URLs
│   ├── build_pipeline.py  Full build workflow (fetch → update → stats)
│   ├── routes/
│   │   ├── jobs.py        /v1/graphify/jobs
│   │   └── graphs.py      /v1/graphify/graphs/{id}/* + /v1/graphify/artifacts/{token}
│   └── main.py            FastAPI factory
├── scripts/
│   ├── start_dev.sh       Uvicorn hot-reload launcher
│   ├── run_tests.sh       Boot server + run smoke test
│   └── smoke_test.py      End-to-end acceptance test
├── requirements.txt
├── .env.example
└── README.md
```

## Security

- **Bearer auth**: every endpoint (except `/health` and `/`) requires
  `Authorization: Bearer <key>`. The comparison is constant-time on
  SHA-256 hashes so a process dump does not leak raw keys.
- **URL allowlist**: `GRAPHIFY_ALLOWED_HOSTS` defaults to public GitHub
  hosts only. `localhost` and `127.0.0.1` are intentionally not on the list.
- **Secret/PII redaction**: sensitive file names (`.env`, `id_rsa`,
  `credentials.json`, …) and known credential paths (`.ssh/`, `.aws/`,
  `.gcp/`, …) are dropped from the corpus before `graphify update` runs.
  Inline `api_key=…` patterns in kept text files are replaced with
  `[REDACTED]`.
- **Audit log**: every job lifecycle event, CLI invocation, and
  signed-URL issue is recorded in `GRAPHIFY_AUDIT_LOG`. The log is
  JSONL, append-only, and secret/PII-redacted.
- **Signed download URLs**: artifact URLs are signed with an HMAC of
  `{job_id, format}` and expire after `GRAPHIFY_URL_TTL_SECONDS`.

## Deployment notes

- Do not put this service behind a reverse proxy that can be reached from
  untrusted networks without additional auth on the proxy.
- Do not allow the GPT Action to call `localhost`. Configure the Action's
  `servers.url` to a reachable HTTPS endpoint.
- Prefer running the `graphify` CLI in a sandbox (container with strict
  seccomp, no network egress except the allowlist, no write to the
  filesystem except the configured `GRAPHIFY_WORK_ROOT`).
- For sensitive corpora, shorten `GRAPHIFY_URL_TTL_SECONDS` to a few
  minutes and reduce `GRAPHIFY_WORK_ROOT` retention via a cron job that
  prunes `./var/workspaces/*` older than the agreed retention window.
