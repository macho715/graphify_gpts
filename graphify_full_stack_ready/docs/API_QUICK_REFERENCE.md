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
