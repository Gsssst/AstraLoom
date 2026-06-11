## Why

Paper Q&A currently says "当前论文内容不足" for questions whose answers exist in PDF tables. Investigation on `Towards One-to-Many Temporal Grounding` shows both failure modes: lightweight `pdfplumber` parsing stores incomplete table rows/headers, and the Q&A retriever can exclude structured table blocks when section-first retrieval is triggered.

## What Changes

- Improve structured PDF parsing quality by preferring a stronger parser path when available and surfacing parser quality signals for table extraction.
- Preserve lightweight parsing as fallback, but stop treating low-quality table extraction as equivalent to high-quality structured parsing.
- Update current-paper evidence retrieval so table/benchmark/metric/reward questions receive structured table and caption evidence in addition to section text.
- Add regression tests using the OMTG-style failure mode where table evidence exists but section-first retrieval would otherwise omit it.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `paper-reader-grounded-interaction`: Structured PDF parsing SHALL provide higher-quality table evidence and expose table quality metadata.
- `paper-qa-evidence-grounding`: Paper Q&A SHALL include table/caption evidence for table-like questions even when section-first retrieval is active.

## Impact

- Affects PDF structured parsing, parser status metadata, current-paper evidence retrieval, maintenance visibility, and focused regression tests.
- No database migration; quality metadata is stored in existing `Paper.metadata_json`.
