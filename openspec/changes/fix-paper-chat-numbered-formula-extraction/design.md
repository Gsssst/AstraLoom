## Context

The current formula-number lane only searches structured formula blocks. If the parser emits inline formula-like text as an early formula block, the fallback "first formula block" can be wrong. Full text and per-page PDF text often preserve the display formula with a trailing `(1)` marker, so retrieval should inspect those sources directly.

## Goals / Non-Goals

**Goals:**
- Detect explicit numbered formula blocks in text sources.
- Preserve page and section context when available.
- Avoid treating ordinary section numbers or citations as formulas.

**Non-Goals:**
- Do not implement complete LaTeX parsing.
- Do not change rendering.
- Do not infer missing formula numbers.

## Decisions

- Add a regex-based text extractor for lines containing math-like syntax and explicit formula labels.
- Search `full_text` and `page_texts` before structured formula blocks for formula-number queries.
- Keep structured formula fallback when no explicit text formula is found.

## Risks / Trade-offs

- Regex extraction can miss multi-line formulas without a number on the same line -> Nearby line context is included to improve matching.
- Some PDFs may split formula and number across columns -> The structured formula fallback remains available.
