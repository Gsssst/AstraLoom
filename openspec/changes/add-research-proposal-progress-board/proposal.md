## Why

Research Ideas now have Copilot discussion, validation, execution packs, and iteration timelines, but the user still has to inspect each Proposal manually to decide what to do next. A progress board will turn those signals into grouped states, priority, blockers, and one-click next actions.

## What Changes

- Add a project-level Proposal progress board API derived from existing Proposal, validation, execution, experiment, and discussion data.
- Classify each Proposal into an actionable status such as needs evidence, needs experiment design, ready for experiment, needs evolution, ready for writing, rejected, or implemented.
- Compute a transparent priority score and recommended next action for each Proposal.
- Add a frontend board tab that groups Proposal cards by status and exposes direct next-step actions.

## Capabilities

### New Capabilities
- `research-proposal-progress-board`: Research projects expose a Proposal progress board with derived status, priority, blockers, and recommended actions.

### Modified Capabilities

## Impact

- Affects `backend/app/api/research.py`, `backend/app/services/research_service.py`, `frontend/src/pages/ResearchProjectPage.tsx`, and focused tests.
- No database migration or new dependency is required.
- Similar-project research: AI-Researcher and related research-agent projects rank, critique, and refine ideas before experiments; project-board style tools group work by next action. This change applies those patterns to existing Proposal lifecycle data.
