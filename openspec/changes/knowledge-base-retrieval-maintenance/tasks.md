## 1. Backend Maintenance API

- [x] 1.1 Add BM25 status reporting to the hybrid search service.
- [x] 1.2 Add fixed admin maintenance routes for health, BM25 rebuild, embedding backfill, full-text backfill, and diagnostics.
- [x] 1.3 Keep maintenance operations bounded and return structured counts.

## 2. Settings UI

- [x] 2.1 Add a knowledge-base maintenance card to the settings data tab.
- [x] 2.2 Show health coverage, stale-index hints, and missing-artifact samples.
- [x] 2.3 Add action buttons and a search diagnostic form with readable result lists.

## 3. Verification

- [x] 3.1 Add backend regression tests for BM25 status, fixed-route ordering, admin protection, health summaries, and diagnostics formatting.
- [x] 3.2 Run OpenSpec validation, backend tests, frontend layout checks, and production build.
