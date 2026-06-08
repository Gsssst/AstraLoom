## Why

The section editor currently compiles a section into its own standalone PDF. For paper writing, users need to see how the active section fits into the full manuscript layout, citations, headings, and surrounding sections.

## What Changes

- Change section-triggered LaTeX PDF preview to compile the assembled manuscript instead of a section-only wrapper.
- Merge the current editor draft into the corresponding manuscript section before compilation so unsaved or just-edited content appears in the preview.
- Keep compile diagnostics, warnings, errors, logs, and authenticated PDF loading behavior unchanged.
- Add response metadata that makes the preview scope clear to the UI.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `writing-manuscript-latex-workbench`: Section-triggered PDF previews should render the full manuscript with the active section draft merged in.

## Impact

- Backend: writing project LaTeX preview service.
- Frontend: writing workbench preview labels.
- Tests: backend preview assembly coverage and frontend contract checks.
