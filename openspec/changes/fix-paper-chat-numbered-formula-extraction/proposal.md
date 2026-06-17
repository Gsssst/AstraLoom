## Why

Questions like "公式 1 的含义是什么" can still retrieve the wrong evidence when structured PDF parsing extracts inline math before the actual numbered display formula. The assistant then explains a 3.1 preliminary inline expression even though the visible numbered formula `(1)` is in section 3.2.

## What Changes

- Extract explicit numbered display formulas from full text and page text using `(n)` / `Eq. n` / `Formula n` markers.
- Prioritize those text-extracted numbered formulas over unlabelled structured formula order fallback.
- Add regression coverage for the observed case where inline 3.1 math precedes the real numbered formula in 3.2.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `paper-qa-evidence-grounding`: Formula-number retrieval must target explicit numbered formulas before inline math or ordinal fallback.

## Impact

- Affects `backend/app/services/paper_chunk_service.py` formula-number retrieval.
- Adds focused backend tests.
- No frontend, API, or database migration is required.
