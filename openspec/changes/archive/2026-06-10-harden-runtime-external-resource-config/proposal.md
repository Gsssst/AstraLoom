## Why

Fresh server deployments can fail embedding generation when the backend container cannot reach `huggingface.co` to download the local sentence-transformers model. Similar runtime network dependencies should be configurable so lab deployments can use mirrors or persistent caches instead of failing behind restricted networks.

## What Changes

- Add runtime HuggingFace endpoint and model cache configuration to backend and worker containers.
- Persist HuggingFace and sentence-transformers caches in Docker volumes so downloaded models survive rebuilds and restarts.
- Make the local embedding model identifier configurable while preserving the current `all-MiniLM-L6-v2` default.
- Document mirror/cache environment variables and the operational check for vector generation failures.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `deployment-readiness`: Production deployments shall support configurable runtime external resource mirrors and persistent model caches.

## Impact

- Affected files: `docker-compose.yml`, `backend/app/core/config.py`, `backend/app/services/embedding_service.py`, `.env.example`, `README.md`, `introduction.md`, `user-manual.md`.
- No database schema changes.
- No API contract changes.
