## Why

The manuscript workbench still feels narrow because the project selector and evidence cards always occupy a full side rail, even when the user wants to focus on drafting. Users need a quick way to temporarily hide supporting context and let the editor breathe.

## What Changes

- Add a collapsible support rail for the manuscript workbench project selector and evidence cards.
- Provide an obvious compact control to collapse and reopen the rail.
- Expand the main manuscript editor area when the rail is collapsed.
- Preserve existing project selection, evidence actions, and responsive behavior.

## Capabilities

### New Capabilities

### Modified Capabilities

- `writing-manuscript-latex-workbench`: The workbench should allow users to collapse supporting panels so active writing gets more horizontal space.

## Impact

- Frontend: `frontend/src/pages/WritingPage.tsx`
- Tests: writing workbench contract tests
- No backend or database changes.
