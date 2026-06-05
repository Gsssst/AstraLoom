## Context

The application currently downloads arXiv PDFs independently in three places: the reader proxy, synchronous full-text preload, and the Celery download task. Each path targets `https://arxiv.org/pdf` directly. The Docker deployment already mounts `/app/uploads` as a persistent volume, so the cache can reuse existing storage without a database migration.

## Goals / Non-Goals

**Goals:**

- Download each arXiv PDF once and reuse it across reading, parsing, and background tasks.
- Allow deployments to configure reachable PDF mirrors ahead of the official origin.
- Fall back to the official arXiv PDF host when configured mirrors fail.
- Reject malformed identifiers and non-PDF responses before persisting them.

**Non-Goals:**

- Changing arXiv metadata API retrieval.
- Shipping an unverified public mirror as a hard-coded default.
- Bypassing publisher access controls for non-arXiv papers.

## Decisions

### Introduce one shared cache service

The cache service owns identifier normalization, candidate URL construction, cache-path generation, response validation, atomic writes, and async cache-miss coalescing. The reader and parser use its async function; Celery uses its synchronous counterpart.

### Configure mirrors separately from the official fallback

`ARXIV_PDF_MIRROR_BASE_URLS` is a comma-separated optional list. `ARXIV_PDF_OFFICIAL_BASE_URL` defaults to `https://arxiv.org/pdf`. Candidate URLs try configured mirrors first and the official base last, deduplicated in order.

### Persist cache files in the existing uploads volume

`ARXIV_PDF_CACHE_DIR` defaults to `./uploads/arxiv-pdfs`. Cache filenames use normalized arXiv identifiers and writes use a temporary sibling file followed by `os.replace`.

### Serve cached files from the backend

The existing PDF proxy route remains stable for the frontend. It resolves the cached path and returns a `FileResponse`, so repeated reader requests avoid upstream downloads.

## Risks / Trade-offs

- [Risk] A public mirror can be unavailable or stale. → Keep mirrors optional, validate PDF bytes, and always retain official fallback.
- [Risk] Multiple workers can miss the same cache concurrently. → Use atomic replacement and per-process async coalescing; duplicate downloads remain harmless across processes.
- [Risk] Cached PDFs consume disk space. → Store files in a dedicated directory so operators can apply ordinary volume cleanup policies later.
