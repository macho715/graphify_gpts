# Graphify GPTS — Custom GPT for Codebase Q&A

A Custom GPT Action that turns any public GitHub repo (or local folder) into a queryable knowledge graph. The GPT then answers architecture, blast-radius, and trace questions by traversing the graph instead of grep.

## What you get

| Component | Purpose |
|---|---|
| `gpts/` | GPT Builder configuration (instructions, knowledge, OpenAPI action schema) |
| `backend/` | FastAPI persistent graphify backend (5/5 smoke test, 35/35 PASS) |
| `vercel_facade/` | Vercel serverless proxy for ChatGPT → backend |
| `INTEGRATION.md` | One-page setup → deploy → use guide |

The active package lives in `graphify_full_stack_ready/`. The legacy hand-rolled prototype (`graphify_backend/`) is intentionally **not** part of this repo — it depended on an external `graphify` CLI that introduced environment-specific failure modes (encoding, `links` vs `edges`, corpus path). The active package ships its own deterministic graph builder (`backend/app/builder.py`) and does not require the CLI at runtime.

## Quick start

### 1. Configure GPT Builder

1. **Configure → Instructions**: paste `graphify_full_stack_ready/gpts/01_GPTS_MAIN_INSTRUCTIONS.md`
2. **Configure → Knowledge**: upload `graphify_full_stack_ready/gpts/02_GPTS_MINI_KNOWLEDGE.md`
3. **Configure → Capabilities**: Web Browsing ON, Data Analysis ON, File Upload ON
4. **Actions → Schema (PoC)**: `graphify_full_stack_ready/gpts/03_OPENAPI_ACTION_SCHEMA_NONE.yaml` (Authentication = None)
5. **Actions → Schema (production)**: `graphify_full_stack_ready/gpts/03_OPENAPI_ACTION_SCHEMA_BEARER.yaml` (Authentication = API Key, Bearer)

### 2. Local backend test

```bash
cd graphify_full_stack_ready/backend
cp .env.example .env
export GRAPHIFY_ALLOW_LOCAL_PATH=true
bash scripts/run_tests_5x.sh
```

Expected: 5 rounds × 7 checks = **35/35 PASS**.

### 3. Deploy

Four options documented in [`INTEGRATION.md`](INTEGRATION.md):

| Option | Best for |
|---|---|
| Railway | **현재 라이브 호스트** — GitHub `main` 자동 배포 (`graphifygpts-production.up.railway.app`) |
| Vercel facade + Railway/Cloud Run | ChatGPT-friendly HTTPS endpoint |
| Docker + Caddy | HVDC/NDA on private infra |
| Cloud Run | GCP-native |

### 4. Try it

```
/graphify https://github.com/octocat/Spoon-Knife.git
```

## Action contract

11 endpoints under `/v1/graphify/`:

- `POST /v1/graphify/jobs` — start a build (`graphifyBuild`)
- `GET /v1/graphify/jobs/{job_id}` — poll status (`graphifyJobStatus`)
- `POST /v1/graphify/graphs/{graph_id}/update` — re-index (`graphifyUpdate`)
- `GET /v1/graphify/graphs/{graph_id}/stats` — god-node candidates (`graphifyStats`)
- `POST /v1/graphify/graphs/{graph_id}/query` — open-ended Q&A (`graphifyQuery`)
- `POST /v1/graphify/graphs/{graph_id}/path` — shortest path (`graphifyPath`)
- `POST /v1/graphify/graphs/{graph_id}/explain` — node explanation (`graphifyExplain`)
- `POST /v1/graphify/graphs/{graph_id}/affected` — blast radius (`graphifyAffected`)
- `POST /v1/graphify/graphs/{graph_id}/export` — **absolute** signed artifact URL (`graphifyExport`); `format:"html"`는 인터랙티브 vis-network graph.html 반환
- `GET /v1/graphify/artifacts/{token}` — public download (`graphifyArtifactDownload`)

Two auth modes:
- **PoC** (`NONE`): open endpoint, no header. Use for local dev / public repos.
- **Production** (`BEARER`): static API key in `Authorization: Bearer <token>`. Required for any non-public content.

## Security

- Allowlist of input hosts: `github.com`, `codeload.github.com`, `raw.githubusercontent.com`, `gist.githubusercontent.com`, `objects.githubusercontent.com`
- Signed artifact URLs (HMAC-SHA256, configurable TTL, default 15 min)
- JSONL audit log with PII/secret regex redaction (`sk-*`, GitHub PATs, JWTs, emails)
- File secret scanner refuses to ingest `.env`, `id_rsa`, `.ssh/`, `.aws/`
- Health and artifact endpoints are unauthenticated; everything else requires Bearer in production mode

## Layout

```
.
├── INTEGRATION.md                              # Setup → deploy → use one-pager
├── README.md                                   # this file
├── .gitignore                                  # excludes deprecated, data, secrets
└── graphify_full_stack_ready/                  # active package (all assets)
    ├── gpts/                                   # GPT Builder config
    ├── backend/                                # FastAPI persistent backend
    │   ├── app/                                # builder, models, auth, audit, security
    │   ├── scripts/                            # run_tests_5x, deploy_*
    │   ├── tests/fixtures/tiny_repo/           # local smoke-test fixture
    │   ├── Dockerfile
    │   ├── Caddyfile
    │   ├── docker-compose.yml
    │   ├── railway.toml
    │   ├── cloudbuild.yaml
    │   ├── cloudrun-service.yaml
    │   └── requirements.txt
    ├── vercel_facade/                          # Vercel serverless proxy
    ├── docs/                                   # architecture, deployment matrix, API ref
    ├── TEST_REPORT.md                          # 5x smoke test (35/35 PASS)
    ├── QUICK_START.md
    ├── MANIFEST.txt
    └── upstream_graphify_reference/            # MIT, only docs (no code dependency)
```

## Verification

- Local smoke test: 5 rounds × 7 checks = **35/35 PASS** (2026-06-17, tiny_repo fixture)
- Live test: `https://github.com/macho715/graphify_gpts.git` (empty repo) — full pipeline ran end-to-end on a real GitHub URL (build → stats → path → explain → affected → export → signed download)
- Live backend (2026-06-17): `https://graphifygpts-production.up.railway.app` — bearer 인증, `invoice_sct` repo 빌드(8,488 nodes / 11,583 edges) → `export html` 절대 URL 다운로드 검증 (vis-network 시각화)

## License

Internal use. No public license declared; this is a private repository.
