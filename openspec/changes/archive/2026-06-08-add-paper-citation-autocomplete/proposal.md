## Why

The LaTeX editor can insert generic `\cite{}` snippets, but users still need to manually look up citation markers from the project evidence cards. Citation autocomplete should use the project's paper/evidence library so writing can stay inside the editor.

## What Changes

- Provide citation suggestions from the selected writing project's evidence cards.
- When the user types inside `\cite{...}`, show matching paper suggestions by marker, title, author, or year.
- Insert the selected citation marker into the cite command.
- Preserve the existing generic LaTeX command suggestions outside citation braces.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `writing-manuscript-latex-workbench`: Section editing should provide paper-aware citation completion from project evidence cards.

## Impact

- Frontend: writing page passes evidence cards to the section editor; section editor adds citation-context completion.
- Tests: writing workbench contract coverage.
