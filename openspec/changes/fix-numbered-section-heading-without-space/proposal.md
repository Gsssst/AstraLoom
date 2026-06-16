## Why

Some parsed PDFs collapse numbered headings and titles into strings such as `3.2.ALVTSFramework` or `3.2.ALVTS Framework`. Paper-detail Q&A currently misses those headings, so explicit requests like "请拆解第 3.2 节" incorrectly fall back to adjacent evidence even though the parsed full text contains the requested section.

## What Changes

- Recognize compact numbered headings where the section number, separator, and title are not separated by whitespace.
- Preserve the conservative guard against treating metrics such as `63.2` as section headings.
- Add regression tests using the observed ALVTS-style parsed heading format.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `paper-qa-evidence-grounding`: Numbered-section retrieval should match compact PDF-extracted headings such as `3.2.ALVTSFramework`.

## Impact

- Affects `backend/app/services/paper_chunk_service.py` numbered heading parsing.
- Adds focused regression tests in `backend/tests/test_paper_reader_grounded_interaction.py`.
- No database migration, frontend change, or new dependency is expected.
