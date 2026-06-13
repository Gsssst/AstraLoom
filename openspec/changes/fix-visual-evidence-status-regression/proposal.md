## Why

Paper library visual evidence status can regress after a successful manual extraction: background processing marks papers failed when parser-located table candidates are later corrected by vision OCR into figures or text-only pages. Older failed papers can also keep stale `fitz unavailable` asset errors after the worker runtime has been fixed.

## What Changes

- Treat vision-corrected non-table candidates as non-tables for readiness checks instead of counting them as missing table OCR.
- Keep manual single-paper extraction and automatic background reconciliation aligned on the same visual evidence success criteria.
- Ensure retry/backfill can overwrite stale visual asset errors such as `fitz unavailable` once page rendering is available.
- Preserve useful OCR text and summaries from misclassified candidates without forcing markdown table output when the image is not actually a table.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `document-visual-evidence-pipeline`: Visual evidence readiness must respect model-corrected element types and stale asset errors must be recoverable by re-extraction.
- `paper-processing-automation`: Background processing must not mark a paper failed when visual OCR has successfully corrected a parser candidate to a non-table item.

## Impact

- Backend: visual evidence normalization, status/readiness counting, and paper processing success checks.
- Tests: backend regression coverage for model-corrected table candidates and stale asset-error retries.
- Runtime: no new dependencies, no new frontend state, and no change to the active system model path.
