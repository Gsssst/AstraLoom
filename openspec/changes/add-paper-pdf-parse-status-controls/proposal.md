## Why

Structured PDF parsing now has lightweight, command, and optional Docling backends, but users cannot see whether a paper was parsed, which parser was used, how much structured evidence was extracted, or rerun parsing when the output is stale. Stable daily use needs observability and a manual repair path.

## What Changes

- Expose structured PDF parse status on paper detail and processing status APIs.
- Add an admin endpoint to force reparse a paper's PDF and refresh structured metadata.
- Surface parser source, page count, block counts, last parsed time, and fallback/error metadata.
- Add a paper detail UI card showing parse readiness and a reparse action for admins.
- Preserve current full-text loading and lightweight fallback behavior.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `paper-reader-grounded-interaction`: Paper detail exposes structured PDF parse status and lets admins rerun parsing.
- `deployment-readiness`: Operators can inspect parser source and failures from the application UI/API.

## Impact

- Affects backend paper APIs, structured PDF metadata persistence, paper detail UI, and focused tests.
- No database migration; status remains derived from `Paper.metadata_json`.
- Admin-only mutation for forced reparse.
