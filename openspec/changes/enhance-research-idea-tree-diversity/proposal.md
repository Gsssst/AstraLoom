## Why

The Research Idea Workbench now has stronger novelty collision checks, but its candidate search tree is still mostly deterministic rule mutation. That improves rigor, yet it does not produce enough true alternative hypotheses or explain why the final selected proposals cover different research paths.

This change upgrades candidate evolution and selection so generated proposals are both stronger and more diverse.

## What Changes

- Add an LLM-assisted critique-and-evolve step for candidate tree expansion.
- Preserve deterministic fallback operators when the model cannot return valid evolved candidates.
- Add diversity-aware reranking before top proposals are persisted.
- Record selection rationale, diversity facets, and suppressed-near-duplicate reasons in the run review summary and selected Idea metadata.
- Surface compact selection rationale in the Proposal detail view.

## Capabilities

### New Capabilities

### Modified Capabilities
- `research-idea-generation-v3`: strengthen candidate search tree behavior and quality signal persistence with LLM-assisted evolution and diversity-aware selection.
- `research-idea-workbench`: expose why selected proposals were chosen and how diversity was preserved.

## Impact

- Backend: `ResearchIdeaWorkbenchService` candidate tree expansion, selection, and persistence.
- Frontend: Proposal detail display for selection rationale and diversity facets.
- Tests: backend workbench tests and frontend contract tests.
- No new database migration is expected because metadata is stored in existing JSON fields.
