## Why

Paper AI answers can contain LaTeX formulas, but the shared Markdown renderer only loads KaTeX after HTML conversion and does not parse Markdown math syntax first. As a result, formulas such as `\tilde{W}_Q = U_Q V_Q` appear as raw text in paper chat instead of rendered math.

## What Changes

- Add a shared Markdown rendering capability for LaTeX math in AI/chat content.
- Parse standard inline and display math delimiters before KaTeX rendering.
- Normalize common model output where display formulas are emitted as bracketed LaTeX blocks instead of valid Markdown math.
- Add a focused frontend contract test and build verification.

## Capabilities

### New Capabilities
- `markdown-content-rendering`: Shared Markdown rendering behavior for AI/chat content, including LaTeX math display.

### Modified Capabilities
None.

## Impact

- Affects the shared frontend Markdown component used by chat, paper detail AI answers, workspace assistant, digests, and writing pages.
- Adds the `remark-math` frontend dependency.
- No backend API, database, or deployment migration is required beyond rebuilding/restarting the frontend after dependency installation.
