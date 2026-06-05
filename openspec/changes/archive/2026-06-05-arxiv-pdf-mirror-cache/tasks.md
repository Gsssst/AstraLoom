## 1. Shared Cache Service

- [x] 1.1 Add arXiv PDF mirror, official fallback, and cache-directory configuration.
- [x] 1.2 Implement shared PDF candidate construction, validation, atomic cache writes, and async cache-miss coalescing.

## 2. Consumer Integration

- [x] 2.1 Serve paper-reader PDF requests from the shared persistent cache.
- [x] 2.2 Reuse cached PDFs during full-text extraction and persist the resolved cache path.
- [x] 2.3 Reuse the shared cache implementation from the Celery paper-download task.
- [x] 2.4 Document mirror configuration in environment templates and Docker forwarding.

## 3. Verification

- [x] 3.1 Add focused regression tests for mirror fallback, cache hits, invalid responses, proxy reuse, and parser reuse.
- [x] 3.2 Run backend, frontend, and strict OpenSpec validation.
