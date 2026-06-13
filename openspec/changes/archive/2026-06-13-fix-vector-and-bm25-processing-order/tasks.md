## 1. Processing Order

- [x] 1.1 Move embedding generation before visual evidence OCR in `process_paper`.
- [x] 1.2 Keep BM25 rebuild before visual evidence so keyword readiness is not blocked by OCR.

## 2. BM25 Status Semantics

- [x] 2.1 Add a database-backed BM25 readiness helper that reports process cache warm state separately.
- [x] 2.2 Use database-backed BM25 status in processing snapshots and maintenance health where a DB session is available.

## 3. Verification and Commit

- [x] 3.1 Add regression tests for embedding-before-visual ordering.
- [x] 3.2 Add regression tests for database-backed BM25 readiness.
- [x] 3.3 Run targeted backend tests and OpenSpec validation.
- [x] 3.4 Restart services if needed and commit the fix.
