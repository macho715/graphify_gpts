# Graphify GPTS Full Stack Ready Pack

판정: 풀옵션 패키지입니다. GPTS instructions/knowledge/action schema, persistent backend, Vercel facade, Docker+Caddy, Railway, Cloud Run, 5회 smoke test를 포함합니다.

## 구성

| Path | 용도 |
|---|---|
| `gpts/01_GPTS_MAIN_INSTRUCTIONS.md` | GPT Builder Instructions 붙여넣기 |
| `gpts/02_GPTS_MINI_KNOWLEDGE.md` | GPT Builder Knowledge 업로드 |
| `gpts/03_OPENAPI_ACTION_SCHEMA_NONE.yaml` | PoC용 Auth=None Action schema |
| `gpts/03_OPENAPI_ACTION_SCHEMA_BEARER.yaml` | 운영용 Bearer Action schema |
| `backend/` | FastAPI persistent Graphify backend |
| `vercel_facade/` | Vercel GPT Action facade/proxy |
| `TEST_REPORT.md` | 제출 전 실행한 5회 이상 smoke test 결과 |

## 빠른 로컬 실행

```bash
cd backend
cp .env.example .env
export GRAPHIFY_ALLOW_LOCAL_PATH=true
bash scripts/start_dev.sh
```

다른 터미널:

```bash
cd backend
bash scripts/run_tests_5x.sh
```

## Docker + Caddy 운영 배포

```bash
cd backend
cp .env.example .env
# 운영이면 .env에서 아래 설정 권장:
# GRAPHIFY_AUTH_MODE=bearer
# GRAPHIFY_ACTION_TOKEN=<random-long-token>
# GRAPHIFY_URL_SECRET=<random-long-secret>
# Caddyfile의 graphify.example.com을 실제 도메인으로 변경
bash scripts/deploy_docker_caddy.sh
```

## Railway 배포 (현재 라이브 — GitHub 자동 배포)

현재 운영: `main` 브랜치 push → 루트 `railway.toml`이 `graphify_full_stack_ready/backend/Dockerfile`로 자동 빌드. 라이브: `https://graphifygpts-production.up.railway.app` (BEARER).

```bash
git push origin main                                          # push = deploy
RAILWAY_TOKEN=<project-token> bash scripts/railway_setup.sh   # 환경 변수 설정 (서비스 레벨)
```

> ⚠️ 아래 CLI 방식은 레거시 — 인터랙티브 로그인이 필요하고 GitHub 자동배포와 충돌 가능:
> ```bash
> # cd backend && railway login && railway link && bash scripts/deploy_railway.sh
> ```

## Vercel Facade 배포

Vercel은 persistent worker가 아니라 GPT Action용 front API로 사용합니다.

```bash
cd vercel_facade
vercel login
vercel env add GRAPHIFY_BACKEND_URL production
vercel env add GRAPHIFY_BACKEND_TOKEN production
# 선택: facade 자체도 보호하려면
vercel env add GRAPHIFY_FACADE_TOKEN production
bash deploy_vercel.sh
```

GPT Action schema의 `servers.url`을 Vercel production URL로 바꿉니다.

## Backend API 예시

```bash
curl -s http://127.0.0.1:8000/health
curl -s -X POST http://127.0.0.1:8000/v1/graphify/jobs \
  -H 'Content-Type: application/json' \
  -d '{"source":{"type":"git","url":"https://github.com/octocat/Spoon-Knife.git"},"options":{"synchronous":true}}'
```

## 민감 데이터 원칙

- 공개 repo: Vercel/Railway/Cloud Run 가능.
- HVDC/NDA, invoice 증빙, 계약서, BOE/BL/DO/CI/PL: private Docker+Caddy backend 또는 GPTS upload-only.
- Auth=None endpoint로 내부 자료 전송 금지.

## 한계

이 패키지는 업로드된 Graphify skill을 GPTS/backend에서 운영 가능하도록 재구성한 deterministic graph backend입니다. `graphifyy` CLI 자체를 필수 runtime dependency로 두지 않아 Vercel/Railway/Docker에서 즉시 실행되도록 만들었습니다. 실제 upstream `graphifyy[all]` CLI와 완전 동일한 semantic extraction이 필요하면 backend worker 내부에 `graphifyy` 설치/실행 adapter를 추가하면 됩니다.
