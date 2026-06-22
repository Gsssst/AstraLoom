## Why

Some paper visual evidence items are seeded from text blocks that mention "Table N" but do not contain the actual table. The vision pass can correctly identify those page assets as figure/text, yet the readiness status still counts the original table candidate as "missing OCR", producing false processing failures.

## What Changes

- Treat vision-corrected non-table items as non-table for readiness and missing-OCR statistics, including already cached visual evidence metadata.
- Mark vision results that report no visible table as corrected text/figure evidence instead of blocking paper processing as table OCR missing.
- Keep true visual tables without markdown counted as missing OCR so real extraction gaps remain visible.
- Add regression coverage for cached metadata where the original parser kind is `table` but the vision model corrected it to `figure` or `text`.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `paper-multimodal-visual-evidence`: Visual evidence readiness distinguishes true table OCR gaps from parser text/caption candidates that a vision model corrected to non-table evidence.

## Impact

- Backend visual evidence normalization and readiness status.
- Paper processing labels and maintenance readiness for visual evidence.
- Backend regression tests for visual evidence status classification.
