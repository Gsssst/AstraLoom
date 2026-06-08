## Why

The paper library is becoming the entry point for research work, but users still need to manually infer whether the database schema is current, which papers are ready for AI workflows, how to filter the library, and how to shape group reports. Recent schema drift also showed that migration health needs to be visible before a normal paper search fails.

## What Changes

- Surface database migration health directly in the paper-library maintenance center and warn when migrations are required.
- Add richer paper-library filters for importer, full-text availability, embedding availability, source, year, and reading state.
- Add selected-paper group-report presets so users can quickly choose default, cross-paper comparison, method lineage, reproduction, or review-style reports while still editing custom instructions.
- Add paper-detail AI insight generation that summarizes contribution, reusable methods, reproducible experiments, limitations, gaps, and research-direction fit for the open paper.
- Add an ingestion/processing status view that shows whether local papers have PDF/full text, embeddings, tags, and queue/repair actions.

## Capabilities

### New Capabilities
- `paper-detail-ai-insights`: AI-generated paper-detail insight cards for contribution, methods, reproducibility, gaps, and research fit.

### Modified Capabilities
- `core-workflow-reliability`: Migration health becomes visible from the paper-library maintenance UI, not only via backend endpoint/logs.
- `paper-discovery-search-and-ingest`: Local search supports richer library filters and exposes processing readiness metadata.
- `paper-library-maintenance-center`: The maintenance center displays migration health and paper processing status/repair actions.
- `paper-bulk-actions-export`: Group meeting reports support selectable report presets in addition to custom prompt text.

## Impact

- Backend: paper search query params, paper brief metadata, maintenance/processing endpoints, paper-detail insight endpoint, report prompt preset handling.
- Frontend: paper library filters, maintenance center status panels, processing queue section, group-report modal presets, paper-detail insight UI.
- Tests: targeted backend tests for filters/status/insights/presets and frontend contract tests for new UI hooks.
