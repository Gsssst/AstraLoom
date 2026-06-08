## Why

Users can bind submission templates, but they currently cannot remove a broken or unwanted template from the writing project. The compile layout selector also sits in the export panel, making it unclear that single-column, double-column, and template choices affect PDF preview.

## What Changes

- Add an action to remove the bound submission template from a writing project.
- Reset LaTeX compile settings to single-column article when a template is removed.
- Move/surface the compile layout control in the manuscript preview area so users can choose single-column, double-column, or template before previewing.
- Keep export behavior using the same saved compile layout.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `writing-submission-template-profile`: Bound templates can be removed safely.
- `writing-manuscript-latex-workbench`: Preview layout selection is visible in the manuscript preview workflow.

## Impact

- Backend: writing project service and writing API route for unbinding template metadata.
- Frontend: writing workbench controls for preview layout and template removal.
- Tests: backend metadata reset and frontend contract coverage.
