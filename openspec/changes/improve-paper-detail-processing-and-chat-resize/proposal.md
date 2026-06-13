## Why

Some paper import paths create `Paper` rows directly, so newly imported papers can sit in “待处理” until the periodic reconciler finds them. On the detail page, the AI Q&A panel can be resized only when the PDF viewer is visible, which makes content-only reading cramped on wide screens.

## What Changes

- Ensure every new paper import path immediately enqueues the automatic processing pipeline instead of waiting for the 10-minute reconciler.
- Persist a queued/running processing marker when a paper is submitted to the processing pipeline so the UI reflects immediate backend work.
- Sanitize PDF extracted text and structured metadata before database writes so invalid NUL bytes do not abort processing.
- Isolate per-paper pipeline failures during reconciliation with rollback so one bad PDF cannot block later papers.
- Dispose async database connections after Celery paper-processing tasks so repeated scheduled runs cannot reuse connections bound to a closed event loop.
- Treat visual evidence as complete only after required table OCR/visual summaries are present, and surface missing render/OCR prerequisites as blocking errors.
- Add tests for BibTeX/Zotero import processing enqueue behavior.
- Make the paper detail AI Q&A panel horizontally resizable even when the PDF panel is hidden.
- Reuse the existing local resize handle pattern; do not add a new frontend dependency.

## Capabilities

### New Capabilities

### Modified Capabilities
- `paper-ingestion`: New papers from direct import endpoints must immediately enter the automatic processing pipeline.
- `paper-detail-chat-parity`: The paper detail AI Q&A panel must be resizable in both PDF and content-only layouts.

## Impact

- Backend paper import routes in `backend/app/api/papers.py`.
- Paper ingestion service queue metadata in `backend/app/services/paper_ingestion.py`.
- Paper processing metadata interpretation in `backend/app/services/paper_processing_pipeline.py`.
- PDF extraction persistence in `backend/app/services/report_service.py`.
- Paper detail layout in `frontend/src/pages/PaperDetailPage.tsx` and `frontend/src/styles/responsive.css`.
- Backend and frontend contract tests.
