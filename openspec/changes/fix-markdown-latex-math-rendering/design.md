## Context

The frontend already depends on `rehype-katex` and imports KaTeX CSS in the shared `Markdown` component, but `react-markdown` never receives `remark-math`. Without the remark parser, math delimiters remain ordinary text and KaTeX has no math nodes to render.

The model can also emit display formulas in a visually bracketed form such as `[ \tilde{W}_Q = U_Q V_Q ]`. That form is common in streamed LLM text but is not valid Markdown math, so simply adding `remark-math` will not fix those responses.

## Goals / Non-Goals

**Goals:**
- Render standard LaTeX math delimiters in shared Markdown content.
- Convert obvious single-line bracketed LaTeX display blocks to valid display math before rendering.
- Avoid converting citations and ordinary bracketed text.

**Non-Goals:**
- Do not implement a custom math parser.
- Do not change backend paper retrieval or model generation prompts in this fix.
- Do not guarantee rendering for every unsupported KaTeX command.

## Decisions

- Use `remark-math` before `rehype-katex`.
  - Rationale: This is the standard `react-markdown` pipeline for Markdown math and matches the existing KaTeX dependency.
  - Alternative considered: Render LaTeX manually after Markdown. This would be fragile and would bypass the existing unified Markdown pipeline.

- Add a small `normalizeMarkdownMath()` helper in the shared Markdown component.
  - Rationale: It keeps compatibility handling close to rendering and applies consistently across chat surfaces.
  - Alternative considered: Prompt the model to always emit `$$...$$`. That is still useful later, but it does not repair existing streamed content or non-compliant model outputs.

- Only normalize isolated bracketed lines containing LaTeX-like signals such as backslash commands, subscripts/superscripts, braces, fractions, sums, Greek commands, or equation operators.
  - Rationale: This avoids breaking citations like `[E1]`, Markdown links, and ordinary prose.

## Risks / Trade-offs

- False positive bracket conversion -> The helper only rewrites whole-line bracketed blocks and requires math-like syntax.
- KaTeX unsupported command errors -> Keep rendering through `rehype-katex`; unsupported syntax may still display imperfectly, but standard paper formulas improve materially.
- Dependency install changes lockfile -> Commit both `package.json` and `package-lock.json` so deployment installs are reproducible.
