## Context

`backend/app/services/embedding_service.py` lazily creates `SentenceTransformer("all-MiniLM-L6-v2")` inside `generate_embedding()`. That function is awaited by dense retrieval, hybrid retrieval, and embedding backfill paths, but the actual model initialization and `encode()` call are synchronous CPU/file/network-cache work. When first triggered from a request handler, the synchronous work can occupy the FastAPI event loop long enough that unrelated endpoints appear down.

## Goals / Non-Goals

**Goals:**
- Keep local embeddings available for dense retrieval and maintenance jobs.
- Ensure first-time model loading and embedding encoding do not block the asyncio event loop.
- Prevent duplicate model loads when concurrent requests hit the cold model.

**Non-Goals:**
- Replace `sentence-transformers` or change the selected embedding model.
- Move all retrieval to Celery.
- Change API response contracts or retrieval ranking behavior.

## Decisions

- Use `asyncio.to_thread()` around the synchronous model load and encode work.
  - Rationale: this is the smallest change that preserves current behavior while preventing event loop starvation.
  - Alternative considered: eager-load the model at startup. That would make startup slower and can still block readiness.

- Protect lazy initialization with a process-local `threading.Lock`.
  - Rationale: `to_thread()` allows multiple concurrent callers; the lock keeps only one thread responsible for creating the singleton model.
  - Alternative considered: an `asyncio.Lock`. It would protect coroutine callers, but the actual shared state is accessed in a worker thread.

## Risks / Trade-offs

- Thread pool work still consumes local CPU/memory while the model loads -> mitigation: only the blocking work moves off the event loop; callers still await the result and existing error handling remains intact.
- First retrieval on a machine without the model cache can still be slow -> mitigation: unrelated endpoints stay responsive, and the existing model/cache behavior is unchanged.
