## Why

LaTeX preview currently fails hard when `pdflatex` is not installed, even though users still need useful source-level diagnostics. The section editor also saves on every keystroke through parent state, causing the full writing workbench to rerender and visibly jump while typing.

## What Changes

- Return a graceful LaTeX preview fallback when `pdflatex` is unavailable.
- Add lightweight source-level LaTeX diagnostics for missing compiler environments.
- Change the section editor to keep local draft state while typing and debounce persistence.
- Keep explicit preview, citation, quality, and AI actions using the latest local draft.

## Capabilities

### New Capabilities

### Modified Capabilities

- `writing-manuscript-latex-workbench`: LaTeX preview should remain useful without a local compiler, and typing in the section editor should not trigger page jumps.

## Impact

- Backend: `latex_processor.py`, writing closed-loop tests.
- Frontend: `SectionEditor.tsx`, `WritingPage.tsx`, frontend contract tests.
- No database changes.
