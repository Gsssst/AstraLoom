## Context

The shared Markdown renderer already normalizes common model math delimiters and uses `remark-math` plus `rehype-katex` for display formulas. Recent CSS changes keep proper KaTeX tags readable, but they cannot fix formulas where the assistant output places a plain `(3)` at the end of the math content instead of using `\tag{3}`.

## Goals / Non-Goals

**Goals:**
- Convert display-math-only trailing numeric labels into KaTeX tags.
- Keep KaTeX tag layout readable by reserving right-side space for the generated tag.
- Keep the normalization conservative so ordinary parenthesized math expressions are not rewritten.
- Preserve fenced code blocks and inline math exactly.

**Non-Goals:**
- Re-extract formulas from PDFs.
- Change paper-chat retrieval, evidence ranking, or answer prompting.
- Add a new Markdown or math rendering dependency.

## Decisions

- Normalize before Markdown parsing in `Markdown.tsx`.
  - Rationale: this is where existing delimiter cleanup already happens, and it keeps the fix shared across paper chat and other Markdown answer surfaces.
  - Alternative considered: prompt the model to always output `\tag{n}`. That is still useful, but frontend rendering must tolerate historical and imperfect model output.
- Restrict rewriting to complete `$$ ... $$` display blocks.
  - Rationale: equation numbers are a display-equation concern; inline math and prose can validly end in `(3)`.
  - Alternative considered: global regex replacement. That would risk corrupting normal prose and inline references.
- Skip blocks that already contain `\tag{...}`.
  - Rationale: existing correct KaTeX tags should not be modified or double-tagged.
- Reserve right padding on tagged KaTeX display HTML.
  - Rationale: KaTeX positions `.tag` absolutely at the right side of `.katex-html`; without reserved space the centered formula body can visually collide with the tag, especially inside narrow chat panels.
  - Alternative considered: make `.katex-display > .katex` full-width again. That preserves tag layout but makes long formula scrolling less predictable after the previous overflow fix.

## Risks / Trade-offs

- A genuinely intentional trailing `(3)` inside a display equation could be converted to a tag.
  - Mitigation: only convert when `(digits)` is the final non-whitespace token of a display block and the block has no existing tag.
- The model may output unusual numbering such as `(A.3)`.
  - Mitigation: start with numeric labels because that matches the current failure and is safest; broaden later if real examples require it.
