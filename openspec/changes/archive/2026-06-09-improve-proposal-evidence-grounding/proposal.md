## Why

Current proposal ranking already considers novelty and general evidence counts, but it does not explicitly explain which proposal claims are supported by which papers. This makes weakly grounded proposals look competitive and gives users less confidence when deciding which idea to discuss or write up.

## What Changes

- Add a proposal evidence-grounding matrix that extracts core claims from each candidate and maps them to relevant evidence papers.
- Score proposal evidence quality using claim coverage, source/category diversity, citation specificity, and gap alignment.
- Penalize proposals whose claims are weakly supported or depend on too few evidence sources, with an explainable quality-adjustment rationale.
- Persist evidence-grounding metadata in proposal review data so the existing research workbench can display it without recomputing the run.
- Keep the change algorithm-focused and reuse the existing Evidence Map, Gap Map, review, and proposal-detail UI.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `research-idea-workbench`: proposal generation SHALL compute and persist claim-level evidence grounding metadata and use it in selection/ranking.

## Impact

- Backend research idea generation service and tests.
- Research proposal detail UI for displaying persisted grounding metadata.
- No new external dependencies, database tables, or public routes.
