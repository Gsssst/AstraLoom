## Why

Core workflow pages still mix full-page spinners, bare empty states, card loading props, and ad-hoc progress indicators. Users can enter a page or start a long operation without a clear sense of whether the system is loading core data, waiting on optional data, empty by design, or actively processing.

## What Changes

- Add shared frontend state-feedback components for page loading, empty states, and long-running operation progress.
- Replace abrupt full-page loading/empty returns on primary workflow pages with PageShell-compatible states that preserve page context.
- Add consistent, actionable empty states for paper, research, research project, and writing workflows.
- Standardize visible progress copy for long-running workbench and writing operations where progress is already available in the frontend.
- Add contract coverage that prevents primary workflow pages from drifting back to inconsistent state feedback.

## Capabilities

### New Capabilities

- `workflow-state-feedback`: Shared frontend loading, empty, and progress feedback patterns for primary research workflows.

### Modified Capabilities

## Impact

- `frontend/src/components/WorkflowState.tsx`
- `frontend/src/pages/PapersPage.tsx`
- `frontend/src/pages/ResearchPage.tsx`
- `frontend/src/pages/ResearchProjectPage.tsx`
- `frontend/src/pages/WritingPage.tsx`
- Frontend contract tests.
- No backend API, database, dependency, or environment changes.
