## Why

Paper-detail AI Q&A can parse structured formula blocks, but formula evidence is currently only treated as ordinary structured evidence. When a user asks about a numbered section that contains equations, the answer can over-report missing formulas and make the method sound unreliable even when surrounding evidence is useful.

## What Changes

- Detect formula/equation-oriented paper questions and numbered-section questions that likely need equation support.
- Prefer relevant structured formula evidence alongside text evidence for section and method explanations.
- Preserve existing table, visual, experiment, and numbered-section retrieval behavior.
- Adjust paper Q&A prompt guidance so local evidence gaps are framed as "this specific formula/detail was not retrieved" instead of implying the method or whole answer is unreliable.
- Add regression tests for formula evidence retrieval and calibrated insufficiency wording.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `paper-qa-evidence-grounding`: Paper Q&A should retrieve formula/equation evidence when relevant and communicate missing formula details as scoped limitations.

## Impact

- Affects `backend/app/services/paper_chunk_service.py` evidence planning and retrieval lanes.
- Affects `backend/app/services/memory_service.py` paper Q&A context wording.
- Adds regression tests in `backend/tests/test_paper_reader_grounded_interaction.py` and/or paper chat parity tests.
- No database migration or new dependency is expected.
