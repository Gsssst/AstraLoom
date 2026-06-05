## Why

arXiv PDF reading and full-text extraction currently download the same remote file through separate code paths, always from the official host. Users in regions with slower international connectivity need configurable mirror fallback and persistent local reuse without changing the authoritative arXiv metadata source.

## What Changes

- Add a shared arXiv PDF cache service with configurable mirror base URLs and official-host fallback.
- Validate arXiv identifiers and downloaded PDF content before writing persistent cache files.
- Serve paper-reader PDF requests from the persistent cache, downloading only on a cache miss.
- Reuse the same cached PDF for full-text parsing and background download tasks.
- Document mirror and cache configuration in the environment template.

## Capabilities

### New Capabilities

- `arxiv-pdf-mirror-cache`: Configurable arXiv PDF mirror fallback and persistent cache reuse for reading and parsing.

### Modified Capabilities

None.

## Impact

- New shared PDF cache service.
- Paper PDF proxy, full-text extraction service, and Celery paper-download task.
- Scholarly configuration, Docker environment forwarding, and regression tests.
