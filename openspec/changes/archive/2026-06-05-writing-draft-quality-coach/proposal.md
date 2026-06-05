## Why

The writing workbench can manage sections, evidence cards, and citation checks, but it does not yet tell users whether a section has a clear claim, enough evidence, comparison, and research gap. This makes the assistant feel like a toolbox instead of a writing coach.

## What Changes

- Add deterministic section quality analysis for writing drafts.
- Expose a section quality check endpoint for writing projects.
- Add quality-check controls and diagnostics to the section editor.
- Surface concrete rewrite guidance for missing claim, weak evidence, missing comparison, missing gap, and thin structure.

## Capabilities

### New Capabilities
- `writing-draft-quality-coach`: Section-level draft quality diagnostics and rewrite guidance for writing projects.

### Modified Capabilities
- None.

## Impact

- Backend: writing project service and writing API.
- Frontend: writing page section editor and contract tests.
- Tests: backend focused tests and frontend contract tests.
- No database migration and no new dependency.
