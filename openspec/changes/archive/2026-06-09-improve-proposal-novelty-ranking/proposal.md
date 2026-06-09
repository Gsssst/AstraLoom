## Why

Research idea generation now uses evidence, Gap Maps, and toolbox context, but novelty checking still relies mostly on coarse candidate-to-paper similarity. This can let proposals that merely rephrase existing work rank too highly.

## What Changes

- Add a facet-level novelty matrix comparing candidate proposals against similar work across research question, mechanism, experiment setup, contribution claim, and evidence overlap.
- Store concise differentiation notes: similar points, real differences, missing differentiation, and manual review risks.
- Use the novelty matrix to strengthen candidate scoring, selection ranking, and adversarial review penalties.
- Add a deterministic repair pass for candidates that are too similar, producing a revised candidate that explicitly avoids the nearest collision when possible.
- Surface the novelty matrix summary in the existing Proposal detail UI.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `research-idea-workbench`: Candidate novelty review, proposal ranking, and persisted proposal metadata should use facet-level novelty analysis instead of only aggregate similarity.

## Impact

- Backend Research Idea Workbench service: novelty check, candidate repair, quality adjustment, selection summary, persisted proposal review metadata.
- Frontend research project page: Proposal detail display of novelty facets and differentiation notes.
- Tests: backend helper tests for novelty matrix/scoring/repair and frontend contract tests for the display.
