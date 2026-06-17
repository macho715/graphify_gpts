# Quick Start — Graphify OS Full Stack

## 1) GPTS Configure

1. GPT Builder → Configure.
2. Instructions: paste `gpts/01_GPTS_MAIN_INSTRUCTIONS.md`.
3. Knowledge: upload `gpts/02_GPTS_MINI_KNOWLEDGE.md`.
4. Capabilities: Web Browsing ON, Data Analysis ON, File Upload ON.
5. Actions:
   - PoC: paste `gpts/03_OPENAPI_ACTION_SCHEMA_NONE.yaml`, Authentication=None.
   - Production: paste `gpts/03_OPENAPI_ACTION_SCHEMA_BEARER.yaml`, Authentication=API Key → Bearer.

## 2) Backend Local Test

```bash
cd backend
cp .env.example .env
bash scripts/run_tests_5x.sh
```

Expected result: `../TEST_REPORT.md` shows 5 rounds, 35 checks, 35 PASS.

## 3) Production Path

- Public repo PoC: Railway or Vercel facade + backend.
- HVDC/NDA: Docker+Caddy private backend with Bearer auth.

## 4) Action Test Prompt

```text
/graphify https://github.com/octocat/Spoon-Knife.git 후 stats/query/explain 테스트
```
