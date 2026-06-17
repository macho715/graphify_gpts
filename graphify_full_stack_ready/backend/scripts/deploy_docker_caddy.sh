#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env. Review GRAPHIFY_AUTH_MODE, GRAPHIFY_ACTION_TOKEN, GRAPHIFY_URL_SECRET before production."
fi
docker compose up -d --build
docker compose ps
