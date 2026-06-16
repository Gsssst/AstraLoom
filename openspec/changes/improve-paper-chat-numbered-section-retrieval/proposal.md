## Why

Paper-detail AI Q&A currently recognizes semantic section names such as Introduction, Method, and Experiments, but it does not treat numbered requests like "第 3.2 节" or "Section 3.2" as a hard retrieval target. As a result, the assistant can retrieve nearby figure captions or adjacent sections and then correctly but unhelpfully report that the exact section content is missing.

## What Changes

- Detect explicit numbered section requests in paper-detail questions, including Chinese and English forms.
- Extract evidence from the requested numbered section up to the next same-or-higher-level section heading when the parsed text contains that range.
- Return numbered-section evidence with metadata indicating the requested section number, matched heading, source type, and extraction confidence.
- If the exact numbered section cannot be located, add a targeted insufficiency warning instead of relying only on generic top-k retrieval.
- Preserve existing semantic section, table, visual, and experiment evidence routes as fallbacks.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `paper-qa-evidence-grounding`: Paper Q&A must prioritize explicitly requested numbered sections before generic top-k retrieval.

## Impact

- Affects `backend/app/services/paper_chunk_service.py` numbered section detection and retrieval.
- Affects paper Q&A evidence metadata generated through `backend/app/services/memory_service.py`.
- Adds regression tests for section-number detection, extraction, and fallback behavior.
- No database migration or new dependency is expected.
