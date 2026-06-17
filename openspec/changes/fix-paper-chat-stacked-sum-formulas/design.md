## Context

PDF text extraction linearizes rendered formulas. For formula 11, the visual expression contains `1/N` and a summation with `i=1` and `N`, but those elements are split across surrounding text lines. The current formula context window intentionally became stricter to avoid pulling prose into formula 2; that exposed a different failure for stacked formulas.

## Goals / Non-Goals

**Goals:**
- Preserve stacked summation/fraction context for numbered formulas.
- Keep prose filtering strict so previous formula 2 fixes do not regress.
- Make the normalized formula explicit in evidence metadata/text when reconstruction is heuristic.
- Avoid treating math fragments as section headings.

**Non-Goals:**
- Do not implement OCR or rendered PDF coordinate parsing.
- Do not reconstruct arbitrary complex formulas.
- Do not change chat prompt wording or frontend layout.

## Design

1. Add helpers for formula layout fragments:
   - summation markers such as `(cid:88)` and `∑`;
   - index bounds such as `i=1`, `j=1`;
   - short denominator/numerator fragments such as `N` and `1 (cid:88)`.
2. Extend numbered formula context collection to include nearby math-fragment lines while still excluding prose.
3. Add a targeted normalization pass for extracted loss formulas where:
   - a formula line contains `L=` and `(S(i)-S*(i))^2`;
   - nearby fragments include `1`, `N`, summation, and `i=1`;
   - output includes a `Normalized formula` line with `L = 1/N sum_{i=1}^N ...`.
4. Ignore math-fragment lines in numbered heading parsing so metadata does not report them as headings.

## Risks / Trade-offs

- Reconstruction is heuristic and limited to common stacked summation patterns. Metadata marks it as normalized so it is not confused with exact raw extraction.
- Including nearby fragments can add noisy lines on heavily garbled pages; the fragment detector is deliberately narrow and only activates around formula evidence.
