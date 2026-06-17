# Deployment Matrix

| Option | Use Case | Files |
|---|---|---|
| GPTS-only | Uploaded ZIP/docs, no persistence | `gpts/*` |
| Vercel facade + Docker backend | GPT Action UX + private worker | `vercel_facade/*`, `backend/docker-compose.yml` |
| Docker+Caddy only | Internal/NDA direct backend | `backend/Dockerfile`, `backend/Caddyfile` |
| Railway | Public repo PoC | `backend/railway.toml` |
| Cloud Run | Managed container worker | `backend/cloudbuild.yaml`, `backend/cloudrun-service.yaml` |

## Recommended HVDC/NDA Path

1. Deploy `backend/` on private Ubuntu VM.
2. Set `GRAPHIFY_AUTH_MODE=bearer`.
3. Put Caddy behind corporate DNS/VPN if possible.
4. Configure GPT Action with Bearer token only after endpoint is private or properly access-controlled.
