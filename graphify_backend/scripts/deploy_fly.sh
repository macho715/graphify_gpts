#!/usr/bin/env bash
# Deploy graphify_backend to Fly.io.
# Prerequisites: `flyctl auth login` once.
set -euo pipefail
cd "$(dirname "$0")/.."

# 1) Create the app + persistent volume (one-time).
flyctl apps create hvdc-graphify-backend || true
flyctl volumes create graphify_data --size 10 --region icn || true

# 2) Set secrets (these never land in source or fly.toml).
if ! flyctl secrets list 2>/dev/null | grep -q GRAPHIFY_API_KEYS; then
  echo "[deploy] generating API key + URL secret"
  API_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
  ADMIN_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
  URL_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(48))")
  flyctl secrets set \
    GRAPHIFY_API_KEYS="$API_KEY" \
    GRAPHIFY_ADMIN_KEY="$ADMIN_KEY" \
    GRAPHIFY_URL_SECRET="$URL_SECRET"
  echo "[deploy] save these locally:"
  echo "  GRAPHIFY_API_KEYS=$API_KEY"
  echo "  GRAPHIFY_ADMIN_KEY=$ADMIN_KEY"
  echo "  GRAPHIFY_URL_SECRET=$URL_SECRET"
fi

# 3) Deploy.
flyctl deploy --primary-region icn
echo
echo "[deploy] URL: https://hvdc-graphify-backend.fly.dev"
