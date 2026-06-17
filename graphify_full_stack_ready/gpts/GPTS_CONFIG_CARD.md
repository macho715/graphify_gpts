# GPTS Configure Card

| Field | Value |
|---|---|
| Name | Graphify OS Full Stack |
| Description | Build, store, query, explain, update, and export code/document knowledge graphs through GPTS + backend Actions. |
| Instructions | Paste `01_GPTS_MAIN_INSTRUCTIONS.md` |
| Knowledge | Upload `02_GPTS_MINI_KNOWLEDGE.md` |
| Capabilities | Web Browsing ON, Data Analysis ON, File Upload ON |
| Actions for PoC | `03_OPENAPI_ACTION_SCHEMA_NONE.yaml`, Authentication=None |
| Actions for production | `03_OPENAPI_ACTION_SCHEMA_BEARER.yaml`, Authentication=API Key → Bearer |

## Test Prompt
```text
/graphify https://github.com/octocat/Spoon-Knife.git 후 stats/query/explain 테스트
```

## Production Warning
For HVDC/NDA corpora, use private Docker+Caddy backend and Bearer auth. Do not send internal docs to a public Auth=None endpoint.
