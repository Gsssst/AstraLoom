## Why

Paper Q&A can still answer numbered formula questions incorrectly when the PDF parser extracts formulas as Unicode text instead of LaTeX. In the observed ALVTS paper, structured formula blocks are empty, formula `(2)` is present in page text as `Q˜ =XW˜⊤, K˜ =XW˜⊤, (2) 3.3...`, and the current fallback incorrectly chooses a nearby prose line as the second page-local formula.

This causes the model to receive the wrong evidence chunk and explain a different formula.

## What Changes

- Make numbered formula label detection tolerate PDF-extracted labels followed by adjacent text such as a section heading.
- Strengthen display formula candidate detection for Unicode math symbols and PDF-extracted equations.
- Prevent page-local formula order fallback from treating explanatory prose fragments as standalone formulas.
- Search a narrow current-page neighborhood for exact numbered formulas to handle reader/extractor page offset.
- Add focused tests using the ALVTS-style extracted text.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `paper-qa-evidence-grounding`: Numbered formula retrieval handles PDF-extracted Unicode formulas and page-offset ambiguity more reliably.

## Impact

- Affects `backend/app/services/paper_chunk_service.py`.
- Adds focused backend regression tests.
- No frontend UI or database migration required.
