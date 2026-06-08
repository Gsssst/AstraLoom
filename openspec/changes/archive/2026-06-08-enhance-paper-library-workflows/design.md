## Context

The existing code already has a database migration health service (`app.services.database_health`), `/api/health/db`, a paper maintenance center, full-text/embedding repair endpoints, paper-detail chat, and selected-paper group reports. This change should reuse those surfaces rather than introduce a second workflow.

Open-source paper managers informed the shape of this work: Paperlib uses tags, folders, smart filters, and AI extensions; PaperMemory exposes search syntax for title/author/year/tag and automates paper organization; document-management workflows commonly show processing stages after import.

## Decisions

- Treat processing readiness as derived state instead of adding a new job table in this pass.
  - `has_pdf`: `pdf_path` or metadata `pdf_url`.
  - `has_full_text`: `full_text` length above the existing 500-character threshold.
  - `has_embedding`: vector field is present.
  - `has_tags`: AI tag field is non-empty.
- Extend local paper search with optional filters:
  - `importer`
  - `has_full_text`
  - `has_embedding`
  - `read_status`
  - existing `source`, year, sort, and owner behavior remain.
- Keep remote scholarly search behavior unchanged. Processing filters apply only to local search.
- Add a bounded `GET /api/papers/processing-status` endpoint for maintenance/queue display and a per-paper `GET /api/papers/{id}/processing-status` endpoint for detail views.
- Add `GET /api/papers/{id}/insights` and cache the generated result in `paper.metadata_json["ai_insights"]` with `generated_at`.
- Use report presets as server-recognized prompt instructions:
  - `default`
  - `compare`
  - `method_lineage`
  - `reproduction`
  - `review`
  The frontend can append editable custom text; the backend combines preset and custom prompt.
- Show database migration health in the existing paper maintenance view by calling `/api/health/db`.

## Risks / Trade-offs

- Derived processing status is simpler and safer than introducing async job persistence, but it cannot show live Celery progress percentages. It still solves the user-facing problem: what is ready, missing, or repairable.
- Insight generation may be slow for long papers; use existing full text if available and a bounded prompt.
- Filtering by `read_status` requires a current user because reading state is stored in `user_papers`; unauthenticated requests return no rows for that filter.
