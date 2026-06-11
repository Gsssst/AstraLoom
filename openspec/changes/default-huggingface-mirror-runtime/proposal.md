## Why

Fresh local and Docker deployments can stall when embedding or reranking first loads a HuggingFace-hosted model. The app already documents `HF_ENDPOINT=https://hf-mirror.com`, but the default Docker Compose and application settings still fall back to direct `huggingface.co` unless the operator sets `.env` manually.

## What Changes

- Default HuggingFace model access to `https://hf-mirror.com` in application settings and Docker Compose.
- Apply the same HuggingFace cache/mirror environment before both embedding and reranker model loads.
- Ignore local model-cache directories created during development.
- Update docs to state that the mirror is now the default and can still be overridden.

## Capabilities

### Modified Capabilities
- `deployment-readiness`: Runtime model downloads use the HuggingFace mirror by default and do not require direct `huggingface.co` access unless explicitly configured.

## Impact

- `backend/app/core/config.py`
- `backend/app/services/embedding_service.py`
- `backend/app/services/hybrid_search.py`
- `docker-compose.yml`
- `.gitignore`
- docs/tests for runtime HF environment
