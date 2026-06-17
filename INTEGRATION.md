# Graphify GPTS — Integration Guide

**활성 패키지**: [`graphify_full_stack_ready/`](graphify_full_stack_ready/) (35/35 PASS 검증)
**deprecated**: [`graphify_backend/`](graphify_backend/) — DEPRECATED.md 참조
**라이브 배포**: Railway `https://graphifygpts-production.up.railway.app` (BEARER, GitHub `main` 자동 배포) — 2026-06-17

---

## 1. 로컬 검증 ✅

```bash
cd graphify_full_stack_ready/backend
cp .env.example .env
sed -i 's/^GRAPHIFY_ALLOW_LOCAL_PATH=.*/GRAPHIFY_ALLOW_LOCAL_PATH=true/' .env
bash scripts/run_tests_5x.sh
```

**결과**: 5 라운드 × 7 체크 = **35/35 PASS** (2026-06-17 검증)
- `1_health` / `2_build_local_fixture` / `3_stats_persistent_graph`
- `4_query_returns_hits` / `5_path_explain_affected`
- `6_export_artifact_download` / `7_update_existing_graph_id`

상세 리포트: `graphify_full_stack_ready/TEST_REPORT.md`

---

## 2. GPT Builder 설정

| 순서 | 위치 | 파일 |
|---|---|---|
| 1 | Configure → Instructions | `graphify_full_stack_ready/gpts/01_GPTS_MAIN_INSTRUCTIONS.md` |
| 2 | Configure → Knowledge | `graphify_full_stack_ready/gpts/02_GPTS_MINI_KNOWLEDGE.md` |
| 3 | Configure → Capabilities | Web Browsing ON, Data Analysis ON, File Upload ON |
| 4 | Actions → Schema (PoC) | `gpts/03_OPENAPI_ACTION_SCHEMA_NONE.yaml` (Auth=None) |
| 4 | Actions → Schema (운영) | `gpts/03_OPENAPI_ACTION_SCHEMA_BEARER.yaml` (Auth=Bearer) |

servers.url은 배포 후 변경:
- **Railway (현재 라이브, BEARER 스키마에 적용 완료)**: `https://graphifygpts-production.up.railway.app`
- Fly.io: `https://hvdc-graphify-backend.fly.dev` (legacy 설정, 미사용)
- Vercel facade: facade URL
- Docker+Caddy: `https://<domain>`

---

## 3. 배포 옵션 4종

### 3.1 Railway (현재 라이브 — GitHub 자동 배포)
현재 운영 방식: **GitHub 리포지토리 연결 자동 배포**. `main` 브랜치에 push하면 루트 `railway.toml`이 `graphify_full_stack_ready/backend/Dockerfile`로 빌드한다. 라이브: `https://graphifygpts-production.up.railway.app` (BEARER).
```bash
# 1) 코드 배포 — push가 곧 배포
git push origin main

# 2) 환경 변수 설정 (Railway 프로젝트 토큰 사용; railway.app/account/tokens)
RAILWAY_TOKEN=<project-token> bash scripts/railway_setup.sh
```

> ⚠️ 아래 CLI 방식(`railway login`/`link`/`up`)은 **레거시**다 — 인터랙티브 로그인이 필요하고 GitHub 자동배포와 충돌할 수 있어 권장하지 않는다.
> ```bash
> # (legacy) cd graphify_full_stack_ready/backend && railway login && railway link && bash scripts/deploy_railway.sh
> ```

### 3.2 Docker + Caddy (HVDC/NDA — 추천)
```bash
cd graphify_full_stack_ready/backend
bash scripts/deploy_docker_caddy.sh
# Caddyfile의 graphify.example.com을 실제 도메인으로 변경 필수
```

### 3.3 Vercel Facade (GPT Action proxy)
```bash
cd graphify_full_stack_ready/vercel_facade
vercel login
vercel env add GRAPHIFY_BACKEND_URL production   # 라이브 백엔드: https://graphifygpts-production.up.railway.app
vercel env add GRAPHIFY_BACKEND_TOKEN production # BEARER 모드일 때
bash deploy_vercel.sh
```

### 3.4 Cloud Run
`backend/cloudbuild.yaml` + `backend/cloudrun-service.yaml` 사용.

---

## 4. 운영 토큰 발급

```bash
# GRAPHIFY_ACTION_TOKEN (Bearer API key)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# GRAPHIFY_URL_SECRET (artifact URL HMAC signing)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# ADMIN_KEY (선택)
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

> ⚠️ **시크릿은 절대 코드에 커밋하지 마세요.** `fly secrets set` / `railway variables set` / `vercel env add`로만 주입.

---

## 5. Action Test Prompt

```
/graphify https://github.com/octocat/Spoon-Knife.git 후
stats / query "what is the structure" / explain "README" / path "README" "index.html" / export html 테스트
```

---

## 6. 트러블슈팅

| 증상 | 원인 / 해결 |
|---|---|
| 401 Unauthorized | `GRAPHIFY_AUTH_MODE=none`인데 GPT Action schema가 `BEARER`를 쓰는 경우. NONE.yaml로 교체. |
| 422 Validation Error | `input_uri`가 allowlist 외 호스트. github.com / codeload.github.com / raw.githubusercontent.com / gist만 허용. |
| 502 Application failed to respond (Railway) | uvicorn이 `$PORT`에 바인딩해야 함(하드코딩 8000 금지). Dockerfile CMD `${PORT:-8000}` + 서비스 도메인 targetPort 일치 필요 (commit 02e5159). |
| export `artifact_url`이 상대경로 | `GRAPHIFY_PUBLIC_BASE_URL` 미설정. 서비스 변수에 `https://graphifygpts-production.up.railway.app` 설정 시 절대 URL 반환. |
| Railway 변수 설정해도 미반영 | `railway_setup.sh`가 `serviceId` 없이 upsert하면 환경 공유변수로만 생성됨 → 서비스 레벨로 설정해야 런타임 주입됨. |
| 5x smoke test 경로 에러 (`\\tmp\\tmp.XXX\\round_1.md` 못 찾음) | 테스트 자체는 35/35 PASS. 통합 리포트 생성 단계의 Windows 경로 정규화 버그. 무시 가능. |
| graphify CLI 의존성 오류 | 이 패키지는 graphify CLI를 사용하지 않음 (자체 builder 내장). pip install fastapi만 필요. |

---

## 7. 보안 체크리스트

- [x] Public repo만 → Vercel/Railway/Cloud Run 가능
- [x] HVDC/NDA/인보이스/계약서 → private Docker+Caddy (BEARER 모드)
- [x] Auth=None endpoint로 내부 자료 전송 금지
- [x] Signed artifact URL (HMAC) with TTL
- [x] URL allowlist (github.com, raw.githubusercontent.com, codeload.github.com, gist)
- [x] JSONL audit log with PII/secret redaction
- [x] File secret scanning (.env, id_rsa, .ssh/, .aws/)

---

**Owner**: HVDC SCM Team
**Last verified**: 2026-06-17 (5x smoke test, 35/35 PASS)
**Live**: 2026-06-17 — Railway 백엔드 라이브(`graphifygpts-production.up.railway.app`), 절대 `artifact_url` + vis-network `graph.html` 적용
