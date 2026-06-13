## 1. OpenSpec and Pipeline Design

- [x] 1.1 Create OpenSpec proposal, design, spec deltas, and implementation tasks.
- [x] 1.2 Validate the change with `openspec validate --strict`.

## 2. Backend Automation

- [x] 2.1 Add a paper-processing automation service that computes artifact labels and missing work for each paper.
- [x] 2.2 Add idempotent single-paper processing that reuses existing full-text, structured parse, visual evidence/OCR, embedding, and BM25 services.
- [x] 2.3 Add Celery tasks and beat schedule for post-ingestion processing and periodic reconciliation.
- [x] 2.4 Trigger post-ingestion processing when papers are created or updated.
- [x] 2.5 Expose compact processing labels through the paper API.

## 3. Frontend Simplification

- [x] 3.1 Show readiness labels in the paper library/detail UI.
- [x] 3.2 Reduce daily-workflow prominence of manual maintenance actions while keeping admin diagnostics reachable.
- [x] 3.3 Remove or hide confusing manual processing counters from normal paper/detail surfaces.

## 4. Verification

- [x] 4.1 Add backend tests for decision logic, idempotency, Celery schedule registration, and ingestion trigger.
- [x] 4.2 Add frontend contract coverage for processing labels and reduced maintenance clutter.
- [x] 4.3 Run targeted backend/frontend tests and OpenSpec validation.
- [x] 4.4 Commit the completed change.
