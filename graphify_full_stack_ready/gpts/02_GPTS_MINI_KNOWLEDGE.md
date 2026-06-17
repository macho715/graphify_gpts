# Graphify OS — Mini Knowledge

## What Graphify Produces
`graphify-out/` contains:
- `graph.json`: full graph data.
- `GRAPH_REPORT.md`: summary, key files/concepts, suggested questions.
- `graph.html`: visual/searchable artifact.

## Core Node Types
- `project`: root repository or corpus.
- `directory`: folder.
- `file`: source/doc/config file.
- `function`, `class`: code symbols.
- `concept`: markdown heading or document concept.
- `config`: JSON/YAML/TOML/INI config.
- `external_import`: imported dependency.

## Core Edge Types
- `CONTAINS`: project/folder contains file/folder.
- `DEFINES`: file defines function/class.
- `IMPORTS`: file imports external module/package.
- `REFERENCES_LOCAL`: file references another local file/module.
- `MENTIONS_CONCEPT`: document file contains concept heading.
- `DECLARES_CONFIG`: config file declares configuration.

## Backend Endpoints
- `POST /v1/graphify/jobs` — build graph from git/zip_url/inline/local.
- `GET /v1/graphify/jobs/{job_id}` — job status.
- `DELETE /v1/graphify/jobs/{job_id}` — cancel job.
- `POST /v1/graphify/graphs/{graph_id}/update` — rebuild/update graph.
- `GET /v1/graphify/graphs/{graph_id}/stats` — stats.
- `POST /v1/graphify/graphs/{graph_id}/query` — search graph nodes.
- `POST /v1/graphify/graphs/{graph_id}/path` — shortest path between refs.
- `POST /v1/graphify/graphs/{graph_id}/explain` — node explanation.
- `POST /v1/graphify/graphs/{graph_id}/affected` — impact radius.
- `POST /v1/graphify/graphs/{graph_id}/export` — json/report/html/zip artifact.
- `GET /v1/graphify/artifacts/{token}` — signed artifact download.

## Deployment Profiles
- GPTS-only: uploaded files, no backend, no cost, no persistent graph.
- Vercel facade + backend: GPT Action endpoint on Vercel, persistent backend elsewhere.
- Docker+Caddy: best for HVDC/NDA and private data.
- Railway/Cloud Run: good for public repo PoC and managed deployment.

## Safe Defaults
- Graphify itself has no API key requirement.
- Backend HTTP auth is optional and separate from Graphify.
- Public endpoint + sensitive data is forbidden.
- `GRAPHIFY_AUTH_MODE=bearer` recommended for production.
