## Why

Formula 1/3/4/5/6 retrieval can work while formula 2 still fails because PDF text extraction may drop or reorder a single right-aligned equation label. In that case the current page evidence contains the math expression but not the explicit `(2)` marker, so numbered-formula retrieval falls back to unrelated prose evidence and the model reports that formula 2 was not found.

## What Changes

- Add a current-page-only fallback for numbered formula questions when preferred page text has math-like display formulas but no matching label.
- Interpret "formula N" on the preferred/current page as the Nth display-like formula on that page only when explicit `(N)` lookup fails.
- Mark fallback evidence metadata so the answer can distinguish exact label matches from page-local order inference.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `paper-qa-evidence-grounding`: Numbered formula retrieval can recover from missing PDF-extracted labels on the current page by using page-local display formula order.

## Impact

- Affects `backend/app/services/paper_chunk_service.py`.
- Adds focused backend tests.
- No frontend or database migration required.
