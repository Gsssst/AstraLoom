## Why

Formula 1 retrieval now works, but formula 2 can still fail when the PDF text extractor places the `(2)` marker inline with surrounding prose or when no structured formula block is available. The answer then says formula 2 was not found even though the visible PDF page contains a clear numbered display equation.

## What Changes

- Recognize parenthesized formula numbers even when they are not the final token on the extracted text line.
- Allow text-extracted numbered formulas to be returned even when structured formula evidence is unavailable.
- Add regression tests matching the ALVTS formula 2 layout: formula line with `(2)` followed by subsequent prose.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `paper-qa-evidence-grounding`: Numbered formula retrieval must find explicit formula markers in extracted text even without structured formula blocks or line-final labels.

## Impact

- Affects `backend/app/services/paper_chunk_service.py`.
- Adds focused backend tests.
- No frontend or database migration is required.
