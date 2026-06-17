## Context

The shared `Markdown` component renders AI answers with `remark-math` and `rehype-katex`. The current output relies on KaTeX defaults and surrounding bubble styles. In narrow paper-chat layouts, a long display equation can be forced into an unreadable wrapped or clipped shape before the user widens the panel.

## Goals / Non-Goals

**Goals:**
- Make display math render as a stable block with bounded width.
- Let long equations scroll horizontally within the Markdown answer.
- Apply the fix to all shared Markdown consumers, including paper chat.

**Non-Goals:**
- Change model prompts or formula extraction.
- Change inline math behavior.
- Add a new math renderer dependency.

## Decisions

- Add global Markdown-scoped CSS for `.katex-display` instead of per-page inline styles. This keeps rendering consistent for paper chat, normal chat, and assistant panels using the same component.
- Use horizontal overflow on display math blocks instead of shrinking fonts dynamically. Scrolling preserves formula readability and avoids distorting dense equations.
- Keep `overflow-wrap: normal` inside KaTeX elements so generic text wrapping rules do not split formulas.

## Risks / Trade-offs

- [Risk] Long equations require horizontal scrolling inside the message bubble. -> This is preferable to broken formula layout and mirrors common documentation behavior.
- [Risk] CSS could affect inline KaTeX if scoped too broadly. -> Scope block scrolling to `.markdown-body .katex-display` and only reset wrapping inside nested KaTeX spans.
