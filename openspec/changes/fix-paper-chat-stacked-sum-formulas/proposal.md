## Why

Some PDF-extracted formulas lose their rendered two-dimensional layout. In the ALVTS paper, formula 11 is visually:

```text
L = 1/N sum_{i=1}^N (S(i) - S*(i))^2
```

but `pdfplumber` extracts nearby lines as `1 (cid:88)`, `L=... (11)`, `This ... N`, and `i=1`. The current numbered formula retriever only sends the middle line to the model, so answers omit the averaging factor and summation.

## What Changes

- Detect stacked summation/fraction fragments around numbered formula lines.
- Include adjacent numerator/denominator/index fragments in formula evidence when they belong to the same rendered formula.
- Add a normalized formula note for common extracted summation patterns so the model receives the intended one-line structure.
- Prevent formula fragments such as `1 (cid:88)` from being recorded as section headings.
- Add regression tests for formula 11-style extraction.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `paper-qa-evidence-grounding`: Numbered formula retrieval preserves stacked summation and averaging context from PDF-extracted formulas.

## Impact

- Affects `backend/app/services/paper_chunk_service.py`.
- Adds focused backend tests.
- No frontend or database migration required.
