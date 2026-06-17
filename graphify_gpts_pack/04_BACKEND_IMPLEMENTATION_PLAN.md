# Graphify GPTS Backend Implementation Plan

## 판정
조건부 예. GPTS 단독으로는 업로드 파일 분석과 `graph.json` 질의까지 가능하지만, Graphify 원형의 local watcher, post-commit hook, persistent incremental update, large repo build는 외부 backend가 필요하다.

## Target architecture

```text
Custom GPT
  ├─ Instructions: 01_GPTS_MAIN_INSTRUCTIONS.md
  ├─ Knowledge: 02_GPTS_MINI_KNOWLEDGE.md
  └─ Action: 03_OPENAPI_ACTION_SCHEMA.yaml
        ↓ HTTPS + Bearer API key
Graphify Backend API
  ├─ job queue / workspace isolation
  ├─ graphify CLI wrapper
  ├─ artifact storage: graph.json, GRAPH_REPORT.md, graph.html
  ├─ query service: BFS/DFS/path/explain/affected
  └─ audit logs / retention / PII policy
```

## Backend requirements

| No | Item | Required behavior | Risk control |
|---:|---|---|---|
| 1 | Auth | Bearer API key or OAuth | reject unauthenticated calls |
| 2 | Workspace | one temp workspace per job | prevent cross-user data leakage |
| 3 | Input | public GitHub URL, archive URL, object storage URI | never fetch private URL without approval |
| 4 | Build | run `graphify extract` or CLI equivalent | timeout, file limits, max bytes |
| 5 | Update | run incremental update on existing graph_id | preserve manifest/hash state |
| 6 | Query | read graph.json, execute traversal | no raw file exfiltration |
| 7 | Artifacts | signed download URLs | expiry + access log |
| 8 | Logs | job status, errors, warnings | redact secrets/PII |

## Suggested backend flow

### Build
1. Validate `input_uri` domain allowlist.
2. Create job_id and workspace.
3. Fetch repo/archive/document.
4. Run secret scan and skip sensitive files.
5. Execute Graphify build.
6. Store `graph.json`, `GRAPH_REPORT.md`, optional `graph.html`.
7. Return `graph_id`.

### Query
1. Load `graph_id/graph.json`.
2. Extract vocabulary from node labels.
3. Expand user question only with vocabulary tokens present in graph.
4. Execute BFS/DFS/path/explain/affected.
5. Return result + evidence list + warnings.

## Minimum CLI mapping

| API operationId | CLI equivalent |
|---|---|
| graphifyBuild | `graphify extract <workspace> --mode standard/deep` |
| graphifyUpdate | `graphify update <workspace>` |
| graphifyQuery | `graphify query "QUESTION" --budget N` |
| graphifyPath | `graphify path "A" "B"` |
| graphifyExplain | `graphify explain "NODE"` |
| graphifyAffected | `graphify affected "NODE" --depth N` |
| graphifyExport | `graphify export <format>` |

## Deployment notes

- Do not expose a backend that can fetch arbitrary internal URLs. Apply URL allowlist.
- Do not pass secrets in query text.
- Do not let GPT Actions call `localhost`; deploy to a reachable HTTPS endpoint.
- Use short artifact retention for confidential corpus.
- For Samsung/SCT or HVDC work, prefer private backend or local CLI + uploaded redacted `graph.json`.

## Acceptance test

1. Upload small public repo/archive to backend.
2. Confirm build job returns `succeeded` and `graph_id`.
3. Call stats; verify nodes/edges > 0.
4. Query an obvious symbol/process; result must cite source_file.
5. Path between two known nodes must be non-empty or explicitly no-path.
6. Export json/html; download URL must expire.
