## Why

The manuscript editor is still a plain text area, so common LaTeX commands require repetitive manual typing. The project can inspect submission templates, but preview/export still compile with a fixed article skeleton, so users cannot switch between single-column and double-column manuscript layouts.

## What Changes

- Add Overleaf-style lightweight LaTeX command suggestions in the section source editor when users type commands such as `\c`.
- Let users configure the active manuscript compile layout as single-column, double-column, or template-informed.
- Make LaTeX preview/export use the selected layout and bound template metadata when rendering the document skeleton.
- Surface the active layout/template state in the writing workbench.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `writing-manuscript-latex-workbench`: The section editor should provide LaTeX command assistance and manuscript previews should honor selected layout.
- `writing-submission-template-profile`: Bound template metadata should inform LaTeX rendering instead of only readiness guidance.

## Impact

- Backend: LaTeX renderer, writing project service preview/export paths, project metadata update.
- Frontend: section editor command suggestions, writing template/layout controls.
- Tests: renderer/layout behavior and writing workbench contract coverage.
