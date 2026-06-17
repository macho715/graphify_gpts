# ⚠️ DEPRECATED — 2026-06-17

이 폴더는 **deprecated** 입니다. 더 이상 사용하지 마세요.

## 대체 패키지

👉 **[`../graphify_full_stack_ready/`](../graphify_full_stack_ready/)** — 검증된 통합 패키지.

| 항목 | 이 폴더 (legacy) | graphify_full_stack_ready |
|---|---|---|
| 빌드 검증 | ❌ (graphify CLI 의존성, 부분 테스트만) | ✅ **35/35 PASS** (5x smoke test) |
| Graph builder | 외부 `graphify` CLI subprocess | 자체 내장 (`backend/app/builder.py`) |
| 배포 옵션 | Fly.io only | Railway / Vercel facade / Docker+Caddy / Cloud Run |
| Auth 모드 | Bearer only | **NONE (PoC) + BEARER (운영) 듀얼** |
| GPT Action schema | 1개 | 2개 (NONE/BEARER) |
| Local fixture | ❌ | ✅ `backend/tests/fixtures/tiny_repo` |
| Vercel facade | ❌ | ✅ `vercel_facade/` |
| 의존성 설치 | `graphify[all]` (graph.json 출력 의존) | pip install fastapi만으로 즉시 실행 |

## 이유

1. **graphify CLI 외부 의존성**: Windows cp949 인코딩, `links` vs `edges` 차이, corpus 경로 등 환경 의존성으로 환경마다 빌드 실패 위험.
2. **단일 배포 경로**: Fly.io 한 곳만 지원 — Railway/Cloud Run/Vercel facade 옵션 없음.
3. **단일 Auth 모드**: GPT Builder PoC 시 NONE 모드 즉시 테스트 불가.

## 이전 작업 보존

이전 작업의 산출물은 보존되지만 **신규 작업 금지**:

- `03_OPENAPI_ACTION_SCHEMA.yaml` → [`../graphify_gpts_pack/03_OPENAPI_ACTION_SCHEMA.yaml`](../graphify_gpts_pack/03_OPENAPI_ACTION_SCHEMA.yaml): schema 초안. 최종 검증본은 `graphify_full_stack_ready/gpts/03_OPENAPI_ACTION_SCHEMA_*.yaml`
- `Dockerfile` + `fly.toml` → Fly.io 배포 참고용으로 보존
- `graphify-out/`, `var/`, `app/`, `tests/`, `scripts/` → 디버깅/참고용 보존

## 마이그레이션

```bash
# 기존 fly.toml에서 graphify_full_stack_ready/backend/Dockerfile + railway.toml 사용으로 전환
cd ../graphify_full_stack_ready/backend
bash scripts/deploy_railway.sh    # 또는 deploy_docker_caddy.sh
```

자세한 통합 가이드는 [`../graphify_full_stack_ready/QUICK_START.md`](../graphify_full_stack_ready/QUICK_START.md) 참조.
