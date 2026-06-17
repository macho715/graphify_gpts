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
