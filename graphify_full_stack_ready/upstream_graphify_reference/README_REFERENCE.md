# Upstream Graphify Reference

This folder contains selected files from the uploaded `graphify-8.zip` used to build the GPTS/backend package:

- `README.md`
- `ARCHITECTURE.md`
- `SECURITY.md`
- `pyproject.toml`
- `skill.md`

The production backend in this package is deterministic and self-contained for immediate deployment. It does not require Graphify API keys. If exact upstream CLI behavior is required, install `graphifyy` inside the backend container and replace/extend `app/builder.py` with a subprocess adapter.
