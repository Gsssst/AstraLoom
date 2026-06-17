## Why

Paper chat answers can still render extracted or model-restated equation numbers as plain trailing text inside display math, for example `... \sum_j A_{ij} (3)`. KaTeX treats that `(3)` as part of the formula body, which makes the equation number crowd or overlap nearby symbols.

## What Changes

- Normalize plain numeric labels at the end of Markdown display math blocks into KaTeX `\tag{n}` syntax before rendering.
- Preserve existing `\tag{...}` equations and avoid changing inline math, code fences, and non-math prose.
- Reserve visible space for KaTeX display equation tags while keeping long-formula horizontal scrolling behavior.

## Capabilities

### New Capabilities

### Modified Capabilities

- `paper-reader-grounded-interaction`: Display formula tags must remain separated even when assistant output uses a plain trailing numeric label.

## Impact

- Frontend shared Markdown rendering.
- Frontend Markdown math contract tests.
- No backend API, PDF parser, or database schema changes.
