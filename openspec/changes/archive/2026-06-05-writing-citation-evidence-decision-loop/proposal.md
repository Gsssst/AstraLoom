## Why

The writing assistant can already recommend citations and check section citations, but users still have to infer whether a paper should be used as supporting evidence, a baseline, background, or a limitation. This iteration turns citation recommendation and section diagnostics into a clearer writing decision loop.

## What Changes

- Add deterministic citation decision metadata to recommendation results.
- Show citation recommendations as role-aware evidence decisions in the writing UI.
- Make section citation diagnostics more actionable by surfacing support status, evidence role, and next-step guidance.
- Keep existing citation recommendation and section-check APIs backward compatible.

## Capabilities

### New Capabilities
- `writing-citation-decision-loop`: Citation recommendation and citation checking UI that explains how evidence should be used and what to do when support is weak.

### Modified Capabilities
- None.

## Impact

- Backend: enrich writing citation recommendation payloads with decision labels/actions derived from existing role and match scoring.
- Frontend: improve the citation recommendation tab and section citation diagnostics.
- Tests: add focused backend and frontend contract coverage.
