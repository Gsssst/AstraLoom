## Why

Paper Q&A can identify a numbered bibliography entry such as reference `[1]`, but it does not provide the in-body citation context needed to explain how that reference relates to the current paper. It also fails to detect top-level section requests such as "第四部分" or "Section 4", especially when PDF extraction merges the heading into a noisy line like `... 4.Experiments`.

## What Changes

- Include body citation context snippets alongside the bibliography entry for numbered reference lookups.
- Recognize Chinese ordinal top-level section requests (`第四部分`, `第 4 节`) and English top-level section requests (`section 4`).
- Recover top-level numbered headings that are embedded mid-line by PDF extraction while avoiding figure captions and reference entries.
- Add focused regression tests using patterns seen in `Number it: Temporal Grounding Videos like Flipping Manga`.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `paper-qa-evidence-grounding`: Numbered reference answers include both bibliography entry evidence and in-body citation context when available.
- `paper-reader-grounded-interaction`: Numbered section retrieval handles top-level section requests and noisy embedded headings from extracted PDF text.

## Impact

- Backend paper retrieval planning and evidence pack generation in `backend/app/services/paper_chunk_service.py`.
- Paper Q&A prompt guidance in `backend/app/services/memory_service.py`.
- Focused regression tests in `backend/tests/test_paper_reader_grounded_interaction.py`.
