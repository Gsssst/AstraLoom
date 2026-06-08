## Why

The manuscript workbench support rail takes too much horizontal space when users are focused on writing. It should behave like the main application sidebar: compact by default, expanded only while the user is interacting with it.

## What Changes

- Make the manuscript project/evidence support rail collapsed by default on desktop.
- Expand the rail on mouse hover and collapse it again when the pointer leaves.
- Keep compact icon affordances and tooltips visible while collapsed.
- Preserve mobile/touch access with an explicit expand button because hover is unavailable.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `writing-manuscript-latex-workbench`: The manuscript support rail layout changes from manually collapsed/expanded to desktop hover-expand behavior.

## Impact

- Frontend: `WritingPage` support rail layout state and contract tests.
- Backend/API: no change.
