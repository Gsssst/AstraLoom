## Why

Idea quality is now limited less by formatting and more by which papers enter the Evidence Map. Users need to inspect and steer the evidence set before Gap Map and Proposal generation so the model does not build ideas from accidental or weakly related papers.

## What Changes

- Add Evidence Map controls for preview runs:
  - evidence count limit
  - pinned evidence paper IDs
  - excluded evidence paper IDs
- Persist the controls in the idea run config.
- Apply the controls before Gap Map extraction and proposal generation.
- Show the active controls and let users pin or exclude Evidence Map items from the research project page.
- Keep defaults compatible with the current flow.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `research-idea-workbench`: Evidence Map preview and continuation shall support user-controlled evidence selection before ideas are generated.

## Impact

- Backend API request models for Gap Map preview and continuation.
- Backend service Evidence Map filtering and config persistence.
- Research project page Evidence Map UI controls.
- Tests for evidence filtering and frontend control wiring.
