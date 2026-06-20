## Why

The research idea output currently exposes many review panels at once, but the core idea is still hard to read, compare, and deepen. Users need the generated ideas to first answer "what exactly should we do and why is it worth doing?", then keep evidence, review, and execution details available without making the page noisy.

## What Changes

- Make each selected proposal prioritize a concise `Idea Brief` that explains the research question, key insight, hypothesis, mechanism, minimum experiment, failure condition, and next actions.
- Add a focused "deepen idea" workflow for a selected proposal that rewrites or updates the brief after attacking novelty, clarifying boundaries, strengthening the mechanism, and designing a smaller validation path.
- Keep detailed review, evidence, novelty, and execution metadata available, but collapse secondary information by default in the proposal detail UI.
- Store the deepening result in proposal review metadata so old proposals continue to render and new proposals can be compared without a database migration.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `research-idea-workbench`: selected proposal details shall prioritize a compact idea brief and support a focused deepening workflow grounded in proposal evidence and review metadata.

## Impact

- Backend service: `backend/app/services/research_idea_workbench.py`
- Backend API: `backend/app/api/research.py`
- Frontend page: `frontend/src/pages/ResearchProjectPage.tsx`
- Tests: `backend/tests/test_research_idea_workbench.py`, `frontend/tests/research-proposal-next-actions-contract.test.mjs`
- OpenSpec: this change adds requirements for proposal brief prioritization and deepening.
