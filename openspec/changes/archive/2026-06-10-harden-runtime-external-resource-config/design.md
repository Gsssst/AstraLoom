## Context

The backend currently lazy-loads `SentenceTransformer("all-MiniLM-L6-v2")`. On a fresh deployment this triggers a runtime download from HuggingFace. In restricted networks the request can fail with `Network is unreachable`, leaving paper embeddings unavailable even though the database and API are healthy.

The project already has configurable mirrors for apt, pip, arXiv API, and arXiv PDF cache. The missing piece is runtime model resource configuration for HuggingFace and persistent model caches in production containers.

## Goals / Non-Goals

**Goals:**
- Allow lab deployments to set a HuggingFace mirror such as `https://hf-mirror.com`.
- Persist HuggingFace/sentence-transformers caches across backend rebuilds and restarts.
- Keep the existing MiniLM embedding behavior and 384-dimensional vector contract by default.
- Document how to diagnose and fix embedding download failures.

**Non-Goals:**
- Changing the embedding dimension or replacing the retrieval algorithm.
- Adding a new embedding provider UI.
- Making external scholarly services fully offline-capable.

## Decisions

- Use standard HuggingFace environment variables (`HF_ENDPOINT`, `HF_HOME`, `TRANSFORMERS_CACHE`, `SENTENCE_TRANSFORMERS_HOME`) in Docker Compose.
  - Rationale: these are recognized by the underlying libraries and do not require custom download code.
  - Alternative considered: manually downloading model files during image build. Rejected because it bakes large mutable model artifacts into the image and still fails in restricted networks without mirror configuration.
- Add a Docker volume mounted at `/app/model-cache`.
  - Rationale: one successful model download should survive container recreation and image rebuilds.
  - Alternative considered: store model cache under uploads. Rejected to keep user uploads separate from runtime model artifacts.
- Add `EMBEDDING_MODEL_NAME` to application settings and use it in the embedding service.
  - Rationale: labs can point to a local path or compatible 384-dimensional model if they pre-stage files.
  - Constraint: changing to a different vector dimension requires a database migration and is not part of this change.

## Risks / Trade-offs

- Mirror availability varies by network -> Keep direct HuggingFace as the default and document override values.
- Cached model files consume disk space -> Store in a dedicated named Docker volume so operators can inspect or prune it deliberately.
- Misconfigured model dimensions can break pgvector writes -> Preserve the default model and document that replacements must remain 384-dimensional unless migrations are added.
