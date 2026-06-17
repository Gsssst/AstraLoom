## Why

Paper chat can still answer the wrong formula for queries like "formula 2" when the paper contains multiple numbered formulas or when the PDF extractor orders earlier math-like content before the visible target formula. The recent inline-label fix makes `(2)` detectable, but it does not disambiguate which `(2)` the user means while reading a specific PDF page.

Mature math/PDF systems avoid this by treating formulas as addressable document objects rather than plain text matches. They attach formula number, page, section, nearby explanatory text, and sometimes coordinates or MathML/LaTeX structure. Paper chat needs the same local-document disambiguation for numbered formula questions.

## What Changes

- Add a paper-chat reading-context signal, starting with the current PDF page, to the ask request.
- Prefer numbered formula evidence on or near the requested/current PDF page before falling back to the first global text match.
- Preserve quote-based behavior: explicit selected PDF text still takes precedence over inferred current page.
- Add regression tests where formula `(2)` appears in an earlier page and again in the user's current 3.2 page.

## Research Notes

- Formula search engines such as Tangent-style systems index formula structure and location instead of relying on plain substring retrieval.
- Math extraction pipelines such as GROBID/Mathpix/LaTeXML expose formulas as structured document artifacts with surrounding context, labels, and page/position metadata when available.
- For this project, the pragmatic first step is page-aware formula routing over existing `page_texts`; later work can add formula-object indexing and coordinate-aware selection.

## Impact

- Affects paper detail chat request payload and backend request model.
- Affects paper evidence retrieval in `backend/app/services/paper_chunk_service.py` and `memory_service.py`.
- Adds backend and frontend contract tests where practical.
- No database migration required.
