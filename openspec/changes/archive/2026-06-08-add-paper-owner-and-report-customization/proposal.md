## Why

The paper library currently behaves like a shared global store: users cannot tell who imported a paper, and there is no "my imports" view. Group meeting reports also use a fixed prompt and Word styling, which makes them hard to adapt to different presentation expectations and produces inconsistent Chinese/English fonts.

## What Changes

- Track the account that imported each paper and show that account as a paper-library tag.
- Add a "我的" paper-library filter that returns papers imported by the current account.
- Backfill all existing papers to the `gst` account label.
- Let users provide custom report instructions from the group-report modal.
- Pass custom instructions into group-report generation so reports can follow alternate structures.
- Export group-report Word documents with Chinese text in SimSun and Latin text in Times New Roman.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `paper-discovery-search-and-ingest`: Paper records expose importer ownership and the library can filter to the current user's imports.
- `paper-bulk-actions-export`: Group-report generation accepts user instructions and produces Word output with stable Chinese/English font settings.

## Impact

- Backend: paper model, Alembic migration, paper ingestion APIs, paper search response, group-report request and report service.
- Frontend: paper-library filters, paper cards, group-report modal.
- Tests: backend service/API contract tests and frontend contract tests.
