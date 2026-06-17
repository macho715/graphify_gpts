# Architecture — Graphify GPTS Full Stack

```text
Custom GPT
  ├─ Instructions + Knowledge
  ├─ Data Analysis for uploaded ZIP/docs
  └─ Action schema
        ↓
Vercel Facade optional
        ↓
Persistent Backend
  ├─ source fetch: git / zip_url / inline_files / local_path
  ├─ security gate: allowlist, sensitive filename skip, inline redaction
  ├─ graph builder: files, folders, functions/classes, configs, concepts, imports
  ├─ storage: graph.json, GRAPH_REPORT.md, graph.html
  ├─ query/path/explain/affected
  └─ signed artifact export
```

## Why Vercel Facade

Vercel Python Functions support ASGI/WSGI apps and FastAPI, but function bundles and runtime filesystem behavior are not a substitute for persistent graph storage. Therefore the recommended production layout is Vercel as GPT Action endpoint and Docker/Caddy or Cloud Run/Railway as worker backend.

## Security

- `GRAPHIFY_AUTH_MODE=none` for local/PoC only.
- `GRAPHIFY_AUTH_MODE=bearer` for production.
- `GRAPHIFY_ACTION_TOKEN` protects backend HTTP API, not Graphify itself.
- `GRAPHIFY_URL_SECRET` signs artifact URLs.
- `GRAPHIFY_ALLOWED_HOSTS` restricts remote fetch hosts.
- `GRAPHIFY_ALLOW_LOCAL_PATH=false` by default.
- `GRAPHIFY_PUBLIC_BASE_URL` — export가 절대 `artifact_url`을 생성할 base URL (라이브: `https://graphifygpts-production.up.railway.app`). 미설정 시 요청 호스트로 폴백.

## Live Deployment (2026-06-17)

- **Railway GitHub 연결 자동 배포**: `main` push → 루트 `railway.toml` → `graphify_full_stack_ready/backend/Dockerfile`.
- 라이브: `https://graphifygpts-production.up.railway.app` (BEARER 인증). 변수는 `scripts/railway_setup.sh`로 주입(서비스 레벨).
- `graph.html` export는 vis-network 인터랙티브 시각화(forceAtlas2Based 물리 · 라벨전파 커뮤니티 · 검색 · 범례 사이드바)를 반환하며, `artifact_url`은 절대 URL.
