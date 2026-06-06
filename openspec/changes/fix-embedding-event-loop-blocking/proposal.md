## Why

Local retrieval can trigger the first `sentence-transformers` model load from an async request path. That load currently runs synchronously on the FastAPI event loop, so a chat/RAG request can stall unrelated APIs such as health checks and login.

## What Changes

- Move local embedding model loading and encoding off the event loop.
- Serialize first-time model initialization so concurrent retrieval requests do not attempt duplicate loads.
- Preserve the existing local embedding model and retrieval API behavior.
- Add regression coverage that embedding generation yields control back to the event loop while the model work is running.

## Capabilities

### New Capabilities

### Modified Capabilities
- `reliable-local-retrieval`: Local dense embedding work must not block unrelated async API handling while the model is loading or encoding.

## Impact

- `backend/app/services/embedding_service.py`
- Backend tests for embedding service async behavior
