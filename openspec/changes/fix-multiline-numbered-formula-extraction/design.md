## Context

The previous formula-number fix added direct text extraction for explicit numbered formulas, but the extraction is still too strict. It requires the marker such as `(2)` to appear at the end of a line and only enters the formula branch when structured candidates exist.

PDF text extraction commonly joins formula markers and following prose onto the same line, or yields no structured formula blocks while preserving the numbered formula in page text.

## Goals / Non-Goals

**Goals:**
- Treat `(n)` as a formula marker when nearby text contains math-like syntax, even if more prose follows.
- Prefer text-extracted numbered formulas before structured fallback regardless of structured candidate availability.
- Preserve the existing safeguards against arbitrary prose numbers.

**Non-Goals:**
- Do not infer formulas from screenshots/OCR in this change.
- Do not change frontend rendering.

## Decisions

- Relax the numbered formula label matcher from line-final `(n)` only to parenthesized `(n)` anywhere in the line, while still requiring math signals in the surrounding window.
- Move text formula extraction outside the `structured_candidates` gate for formula-number questions.

## Risks / Trade-offs

- Parenthesized prose numbers could be mistaken for formulas -> The extractor still requires math syntax in the local window.
- Multi-column text order may remain imperfect -> Page text and full text are both checked, with structured fallback retained.
