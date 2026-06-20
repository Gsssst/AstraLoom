## Why

Generated research proposals can read like loose prose: the hypothesis, method, experiment, risks, and evidence are present but not separated enough for users to judge or act on. This makes promising ideas feel vague and hard to compare.

## What Changes

- Require candidate generation to produce a richer structured proposal outline: problem framing, core mechanism, technical steps, expected contribution, experiment plan, risk boundary, and evidence rationale.
- Persist that outline on selected `ResearchIdea` records without breaking existing fields such as `description`, `approach`, `hypothesis`, and `experiment_plan`.
- Render proposal details with clear sections and evidence/risk bullets when the outline is available, while preserving fallback rendering for older ideas.
- Add tests to prevent regression to vague single-paragraph proposals.

## Capabilities

### New Capabilities

### Modified Capabilities
- `research-idea-workbench`: selected proposals store and display detailed structured outlines rather than relying only on loose text fields.

## Impact

- Backend: `backend/app/services/research_idea_workbench.py`
- Frontend: `frontend/src/pages/ResearchProjectPage.tsx`
- Tests: research workbench backend tests and frontend contract tests
