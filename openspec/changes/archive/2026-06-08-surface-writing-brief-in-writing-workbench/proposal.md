## Why

Research Proposals can now produce a bounded writing brief, but the Writing workbench does not yet turn that brief into visible writing constraints. Users can create a draft from a Proposal and then lose sight of its title candidates, contribution chain, claim-evidence map, unsupported claims, and evidence gaps while editing sections.

## What Changes

- Surface the saved Proposal writing brief inside the paper Writing project workbench.
- Show concise readiness signals for claim support, unsafe claims, evidence gaps, and outline coverage.
- Add a dedicated writing-brief panel that presents title candidates, abstract draft, contribution chain, section outline, claim-evidence map, unsafe claims, limitations, and evidence gaps.
- Add quick actions that copy title/abstract/claim text, jump to evidence, and route unsupported claims toward citation/evidence checks.
- Fold writing-brief risks into the workbench blockers/next-action surface so unsupported Proposal claims remain visible before polishing or export.
- No breaking API changes.

## Capabilities

### New Capabilities

### Modified Capabilities
- `research-to-writing-evidence-bridge`: Writing projects created from research Ideas must surface their preserved writing brief in the Writing workbench.

## Impact

- Frontend: `frontend/src/pages/WritingPage.tsx`, focused contract tests.
- Backend: expected to reuse existing writing project metadata; no schema migration planned.
- OpenSpec: delta spec for `research-to-writing-evidence-bridge`.
- External learning: GitHub projects/papers around ScholarCopilot-style context-aware citation suggestions, RefChecker-style claim support checking, and research-workflow assistants informed the decision to expose existing claim/evidence constraints before adding heavier automated fact checking.
