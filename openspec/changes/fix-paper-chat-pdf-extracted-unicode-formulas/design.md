## Context

The failing paper has no structured formula blocks, so formula retrieval depends on `pdfplumber` page text. The desired formula is extracted as:

```text
Q˜ =XW˜⊤, K˜ =XW˜⊤, (2) 3.3.TokenSelectorOptimization
Q K
```

The previous regex ignored `(2)` because it was followed by `3.3`, and the page-local fallback counted a context sentence ending in `X =` as an independent display formula.

## Goals / Non-Goals

**Goals:**
- Prefer exact numbered formula labels whenever they exist in page text.
- Handle Unicode math symbols such as `˜`, `⊤`, `∈`, `×`, and compact PDF-extracted expressions.
- Keep page-local order fallback bounded and high-confidence.
- Cover one-page reader/extractor offsets without broad global inference.

**Non-Goals:**
- Do not add OCR or a full rendered formula detector.
- Do not rewrite the whole paper RAG pipeline.
- Do not change the paper detail UI in this fix.

## Design

1. Update formula label parsing so `(2)` is accepted when followed by whitespace, punctuation, a section heading, or end of line. This covers formula labels that PDF extraction concatenates with following heading text.
2. Add a stronger display-formula heuristic:
   - requires an equation operator or formula function;
   - rewards Unicode math symbols and compact variable expressions;
   - rejects prose-led context lines like `Given the input sequence X =`.
3. Keep adjacent short math-only continuation lines near the formula block, but do not let them create standalone candidates.
4. For explicit numbered formula questions, search pages in this order:
   - exact current/preferred page;
   - exact neighboring pages within one page;
   - page-local order fallback on preferred/neighborhood pages;
   - exact labels elsewhere;
   - full text.
5. Mark neighborhood matches with metadata so references can explain how retrieval was routed.

## Risks / Trade-offs

- Heuristic formula detection remains imperfect for heavily garbled PDFs, but exact label matching now handles the observed failure before fallback.
- Neighbor-page search may find a nearby formula with the requested number even when the current page is stale. Restricting it to exact label matches before order fallback reduces wrong inferences.
