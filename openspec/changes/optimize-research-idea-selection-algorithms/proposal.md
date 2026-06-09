## Why

The research idea workbench already exposes many workflow surfaces, but the core candidate selection still relies on relatively shallow heuristics in several places. The next improvement should make generated ideas more defensible by improving ranking, deduplication, novelty, evidence coverage, and diversity algorithms without adding more UI.

## What Changes

- Improve candidate deduplication so near-duplicate proposals are detected with title, hypothesis, gap, approach, experiment, and evidence overlap rather than a single token Jaccard score.
- Prefer the stronger candidate when duplicates are merged instead of keeping whichever candidate appeared first.
- Add evidence-coverage profiling for each candidate, including seed/background/inspiration balance, source diversity, and linked evidence count.
- Adjust candidate quality scores with explicit evidence coverage, experiment completeness, novelty collision, adversarial review, and gap alignment signals.
- Improve diverse proposal selection so final ideas cover different gaps, operators, evidence clusters, datasets, and risk profiles.
- Persist the new algorithm metadata in existing run summaries and selected idea review metadata.

## Capabilities

### New Capabilities

### Modified Capabilities

- `research-idea-generation-v3`: existing idea generation SHALL use stronger deterministic algorithms for duplicate merging, evidence-aware scoring, novelty risk adjustment, and diversity-aware final selection.

## Impact

- Backend service: `backend/app/services/research_idea_workbench.py`.
- Backend tests: focused deterministic tests for candidate similarity, duplicate replacement, evidence coverage, quality adjustment, and selection diversity.
- OpenSpec only; no backend schema migration, no new API routes, no new frontend screens, and no new external dependencies.
