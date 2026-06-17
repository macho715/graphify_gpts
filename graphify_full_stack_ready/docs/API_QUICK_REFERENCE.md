# API Quick Reference

## Build

```json
POST /v1/graphify/jobs
{
  "source": {"type": "git", "url": "https://github.com/octocat/Spoon-Knife.git"},
  "options": {"synchronous": true}
}
```

## Query

```json
POST /v1/graphify/graphs/{graph_id}/query
{"query": "validate invoice", "limit": 10}
```

## Affected

```json
POST /v1/graphify/graphs/{graph_id}/affected
{"query": "src/invoice.py", "direction": "both", "max_depth": 2}
```

## Export

```json
POST /v1/graphify/graphs/{graph_id}/export
{"format": "zip"}
```

Formats: `json` / `report` / `html` / `zip`. `html`은 인터랙티브 vis-network `graph.html`(라벨전파 커뮤니티 색상 · 검색 · Node Info/Neighbors · 범례 체크박스)을 반환한다.

```json
POST /v1/graphify/graphs/{graph_id}/export
{"format": "html"}
```

응답의 `artifact_url`은 **절대 URL**이다 — 예: `https://graphifygpts-production.up.railway.app/v1/graphify/artifacts/<token>` (HMAC 서명, 기본 1시간 TTL). base는 `GRAPHIFY_PUBLIC_BASE_URL`로 고정한다.

## Download

```
GET /v1/graphify/artifacts/{token}    # 서명된 공개 다운로드 (graph.html / zip / json / report)
```
