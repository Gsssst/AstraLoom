## Why

The writing workbench currently reports LaTeX compile diagnostics but does not show the generated PDF. Users interpret "preview" as a visible compiled manuscript, so a successful check without a PDF feels like compilation still failed.

## What Changes

- Persist a temporary PDF artifact when section or manuscript LaTeX compilation succeeds.
- Return a preview URL in the existing LaTeX preview response.
- Render the compiled PDF inline in the writing workbench while retaining warnings, errors, and logs.
- Keep fallback diagnostics unchanged when `pdflatex` is unavailable or compilation fails.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `writing-manuscript-latex-workbench`: LaTeX preview checks should include a visible PDF preview when compilation succeeds.

## Impact

- Backend: `latex_processor`, writing API static preview route, writing project preview service.
- Frontend: writing page / section editor preview diagnostic panel.
- Tests: backend compile artifact coverage and frontend contract checks.
