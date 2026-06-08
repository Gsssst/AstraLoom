## Why

Successful LaTeX previews can produce many warnings such as undefined references. Showing every warning inline makes the manuscript workbench look noisy even when PDF generation succeeds.

## What Changes

- Keep warning counts visible in LaTeX diagnostics.
- Collapse warning details by default in section and manuscript preview panels.
- Continue showing actual compile errors inline.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `writing-manuscript-latex-workbench`: LaTeX warning details should be available without dominating the preview surface.

## Impact

- Frontend: section editor and manuscript diagnostic panel rendering.
- Tests: writing workbench contract coverage.
