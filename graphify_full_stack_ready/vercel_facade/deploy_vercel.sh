#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
vercel link --yes
vercel deploy --prod
