# Deployment Matrix

| Option | Use Case | Files |
|---|---|---|
| GPTS-only | Uploaded ZIP/docs, no persistence | `gpts/*` |
| Vercel facade + Docker backend | GPT Action UX + private worker | `vercel_facade/*`, `backend/docker-compose.yml` |
| Docker+Caddy only | Internal/NDA direct backend | `backend/Dockerfile`, `backend/Caddyfile` |
| Railway | **현재 라이브 프로덕션** — GitHub `main` 자동 배포 | 루트 `railway.toml` → `backend/Dockerfile` |
| Cloud Run | Managed container worker | `backend/cloudbuild.yaml`, `backend/cloudrun-service.yaml` |

> **현재 라이브 (2026-06-17)**: Railway — `https://graphifygpts-production.up.railway.app` (BEARER, GitHub `main` 자동 배포). 변수는 `scripts/railway_setup.sh`로 주입(서비스 레벨).

## Recommended HVDC/NDA Path

1. Deploy `backend/` on private Ubuntu VM.
2. Set `GRAPHIFY_AUTH_MODE=bearer`.
3. Put Caddy behind corporate DNS/VPN if possible.
4. Configure GPT Action with Bearer token only after endpoint is private or properly access-controlled.
