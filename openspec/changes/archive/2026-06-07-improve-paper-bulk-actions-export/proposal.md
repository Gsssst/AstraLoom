## Why

The paper library already supports selection, collections, reading status, and exports, but selected-paper actions are crowded and inconsistent. Users need a clearer bulk workflow for moving papers into downstream research and writing tasks without manually repeating single-paper actions.

## What Changes

- Replace the current floating selected-paper bar with a structured bulk action bar.
- Add client-side export for selected papers in BibTeX, Markdown, and JSON using already-loaded paper metadata.
- Add bulk reading-status changes for selected local papers by reusing the existing per-paper read-status API.
- Keep and refine bulk add-to-collection, new-collection, batch tag, and group-report entry points.
- Add clear success/failure summaries for multi-step bulk operations.
- Keep destructive deletion out of the first bulk iteration; single-paper delete confirmation remains unchanged.

## Capabilities

### New Capabilities
- `paper-bulk-actions-export`: Defines selected-paper bulk action behavior, export formats, and operation feedback in the paper library.

### Modified Capabilities

## Impact

- `frontend/src/pages/PapersPage.tsx`
- `frontend/src/styles/responsive.css`
- Frontend contract tests.
- No backend API, database, dependency, or environment changes.
