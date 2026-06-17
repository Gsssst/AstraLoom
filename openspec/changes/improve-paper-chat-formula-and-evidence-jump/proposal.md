## Why

Paper chat still has two reader-friction issues: long displayed equations can render with their equation number squeezed into the formula body, and answer evidence markers like `[E1]` are plain text even when the evidence has a PDF page. Users need formulas to remain legible and evidence markers to jump directly to the cited PDF location.

## What Changes

- Refine Markdown/KaTeX display math CSS so equation tags keep their right-side layout while long formulas remain horizontally scrollable.
- Render paper-chat answer evidence markers (`[E1]`, `[E2]`, etc.) as clickable source chips when the marker maps to a paper evidence reference.
- Clicking a source chip navigates the PDF reader to the evidence page and opens/highlights the matching evidence context where available.

## Capabilities

### New Capabilities

### Modified Capabilities

- `paper-reader-grounded-interaction`: Paper-chat evidence references must support direct PDF page navigation.
- `paper-qa-evidence-grounding`: Inline answer evidence markers must be linked to structured evidence references when page metadata is available.

## Impact

- Frontend Markdown rendering and paper detail chat rendering.
- Frontend tests for math layout and evidence marker navigation.
- No backend API or database schema changes.
