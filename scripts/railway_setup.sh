#!/usr/bin/env bash
# One-shot Railway setup script.
# Usage: RAILWAY_TOKEN=<token> bash scripts/railway_setup.sh
# Token: https://railway.app/account/tokens (create "Graphify Setup" token, expires 1h)

set -euo pipefail

: "${RAILWAY_TOKEN:?Set RAILWAY_TOKEN env var (https://railway.app/account/tokens)}"

PROJECT_ID="cf284212-7e0b-4561-8312-8aa1bc3e4664"
ENV_ID="ff60f790-8497-4a9b-85ae-46a524b917b8"
SERVICE_ID="96c2aa52-1976-4eab-883f-4bc5fdd2d8e8"
PUBLIC_BASE_URL="https://graphifygpts-production.up.railway.app"
GQL="https://backboard.railway.app/graphql/v2"

# Fresh tokens
ACTION_TOKEN=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
URL_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

upsert() {
  local name="$1"
  local value="$2"
  echo "  → $name"
  curl -sS -X POST "$GQL" \
    -H "Authorization: Bearer $RAILWAY_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$(python -c "
import json
print(json.dumps({
  'query': 'mutation variableUpsert(\$input: VariableUpsertInput!) { variableUpsert(input: \$input) }',
  'variables': {'input': {
    'projectId': '$PROJECT_ID',
    'environmentId': '$ENV_ID',
    'serviceId': '$SERVICE_ID',
    'name': '$name',
    'value': '''$value'''
  }}
}))")" > /dev/null
}

echo "[1/2] Setting 9 service-level variables…"
upsert GRAPHIFY_AUTH_MODE        bearer
upsert GRAPHIFY_ACTION_TOKEN     "$ACTION_TOKEN"
upsert GRAPHIFY_URL_SECRET       "$URL_SECRET"
upsert GRAPHIFY_ALLOW_LOCAL_PATH false
upsert GRAPHIFY_MAX_FILES        20000
upsert GRAPHIFY_MAX_TOTAL_BYTES  524288000
upsert GRAPHIFY_URL_TTL_SECONDS  3600
upsert PORT                      8000
upsert GRAPHIFY_PUBLIC_BASE_URL  "$PUBLIC_BASE_URL"

echo "[2/2] Reading service domain…"
DOMAIN=$(curl -sS -X POST "$GQL" \
  -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query { project(id: \"cf284212-7e0b-4561-8312-8aa1bc3e4664\") { services { edges { node { name domains { serviceDomains { domain } } } } } } }"
  }' | python -c "
import json, sys
try:
    d = json.load(sys.stdin)
    for e in d['data']['project']['services']['edges']:
        for sd in e['node']['domains']['serviceDomains']:
            if sd['domain']:
                print(sd['domain'])
                sys.exit(0)
except Exception as ex:
    print('ERR:', ex, file=sys.stderr)
print('(domain not yet provisioned — check Railway dashboard)')
")

echo ""
echo "=== Result ==="
echo "ACTION_TOKEN=$ACTION_TOKEN"
echo "URL_SECRET=$URL_SECRET"
echo "DOMAIN=${DOMAIN:-<check Railway dashboard>}"
echo ""
echo "Save ACTION_TOKEN and URL_SECRET. Service will auto-redeploy."
