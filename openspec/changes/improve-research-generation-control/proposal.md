## Why

Generating candidate Proposals in a research direction is a long-running staged workflow, but the current page gives users limited control once generation starts. Users need clearer progress, a way to stop mistaken or slow runs, and an immediate retry path when a run fails.

## What Changes

- Add cancellation support for running Research Idea Workbench stream requests.
- Persist cancelled runs with a user-readable status instead of leaving them ambiguous.
- Improve the research project page generation card with clearer status, active stage, stop control, failure/cancel feedback, retry action, and completion next steps.
- Keep existing staged generation semantics and artifacts intact.

## Capabilities

### New Capabilities

### Modified Capabilities
- `research-idea-workbench`: Workbench runs should be stoppable, recoverable, and clearer about failed/cancelled/completed states.

## Impact

- Backend research run stream lifecycle and run status persistence.
- New authenticated cancel endpoint for project-owned idea runs.
- Frontend generation controls and workbench status UI in `ResearchProjectPage`.
- Backend and frontend regression tests.
