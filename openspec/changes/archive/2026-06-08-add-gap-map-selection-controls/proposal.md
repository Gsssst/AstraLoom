## Why

The Workbench can now generate stronger and more diverse proposals, but it still automatically moves from Gap Map extraction into candidate generation. If the extracted gaps do not match the user's research intent, the downstream proposal search remains biased even when ranking and novelty checks are strong.

This change adds a human-in-the-loop Gap Map checkpoint so users can choose which gaps and generation constraints should guide the proposal search.

## What Changes

- Add a Gap Map preview workflow that stops after evidence and gap extraction.
- Allow users to select preferred gaps, deprioritize irrelevant gaps, and provide a focus note.
- Add generation constraints for research mode, risk appetite, and resource budget.
- Continue idea generation from the selected Gap Map and constraints.
- Persist selected gap metadata and constraints in the run configuration, review summary, and selected proposal metadata.
- Keep the existing one-click generation path working by using all gaps and default constraints when no selection is provided.

## Capabilities

### New Capabilities

### Modified Capabilities
- `research-idea-workbench`: add a user-controlled Gap Map checkpoint and continuation flow.
- `research-idea-generation-v3`: bind candidate generation and final selection rationale to selected gaps and user constraints.

## Impact

- Backend: Research Idea Workbench run lifecycle, APIs, service pipeline, and persisted run metadata.
- Frontend: Research project workbench controls around Gap Map selection and generation constraints.
- Tests: backend workbench tests and frontend contract tests.
- No database migration is expected because selections and constraints fit existing JSON columns.
