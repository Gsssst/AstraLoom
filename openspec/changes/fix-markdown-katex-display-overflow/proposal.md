## Why

Long LaTeX display equations in AI answers can visually collapse or wrap incorrectly when the paper chat panel is narrow. Users should be able to read the same equation reliably regardless of the current chat panel width.

## What Changes

- Preserve KaTeX display equations as intact horizontal blocks inside Markdown-rendered AI answers.
- Allow long formulas to scroll horizontally inside the answer bubble instead of being squeezed into broken text.
- Keep normal prose, inline math, tables, and code rendering behavior unchanged.

## Capabilities

### New Capabilities

### Modified Capabilities

- `paper-reader-grounded-interaction`: AI answer rendering must keep display equations readable in constrained chat widths.

## Impact

- Affected frontend: shared Markdown renderer styles and paper chat display.
- No backend API or database changes.
- No new dependencies.
