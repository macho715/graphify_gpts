# Graphify GPTS — Integration Guide

**활성 패키지**: [`graphify_full_stack_ready/`](graphify_full_stack_ready/) (35/35 PASS 검증)
**deprecated**: [`graphify_backend/`](graphify_backend/) — DEPRECATED.md 참조

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
- Railway: `https://<app>.up.railway.app`
- Fly.io: `https://hvdc-graphify-backend.fly.dev` (legacy 설정)
- Vercel facade: facade URL
- Docker+Caddy: `https://<domain>`

---

## 3. 배포 옵션 4종

### 3.1 Railway (PoC 추천)
```bash
cd graphify_full_stack_ready/backend
railway login
railway link
railway variables set GRAPHIFY_AUTH_MODE=bearer \
  GRAPHIFY_ACTION_TOKEN=$(python -c "import secrets; print(secrets.token_urlsafe(32))") \
  GRAPHIFY_URL_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
bash scripts/deploy_railway.sh
```

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
vercel env add GRAPHIFY_BACKEND_URL production   # e.g. https://hvdc-graphify-backend.railway.app
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
