## Why

Proposal ranking currently checks experiment completeness with a coarse dataset/baseline/metric/step heuristic. That lets proposals with vague experiments, weak baselines, missing ablations, or unrealistic compute assumptions rank too highly.

## What Changes

- Add a deterministic experiment quality profile for each candidate proposal.
- Score dataset clarity, baseline strength, metric alignment, ablation design, statistical validity, failure analysis, and compute feasibility.
- Penalize proposal ranking when the minimum experiment is not strong enough to falsify the claim.
- Persist experiment evaluation metadata in proposal review data for downstream validation and writing.
- Display a compact experiment quality summary in the existing proposal detail view.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `research-idea-workbench`: proposal review and selection SHALL use a richer experiment-plan evaluation profile.

## Impact

- Backend research idea generation scoring and tests.
- Research project proposal detail UI.
- No database schema changes, new dependencies, or new routes.
