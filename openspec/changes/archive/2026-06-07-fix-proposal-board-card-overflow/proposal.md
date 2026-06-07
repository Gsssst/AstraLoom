## Why

Long blocker text in the Proposal progress board currently renders as non-wrapping tags and can overflow beyond the Proposal card boundary. This makes the board hard to scan and visually broken on desktop and narrow layouts.

## What Changes

- Constrain Proposal board card content so titles, summaries, blockers, signals, and actions stay within the card.
- Render blocker text as wrapping inline chips/alerts instead of nowrap tags.
- Add focused frontend contract coverage for card overflow constraints.

## Capabilities

### New Capabilities

### Modified Capabilities
- `research-proposal-progress-board`: Board cards must keep dynamic text and actions within card boundaries.

## Impact

- Affects `frontend/src/pages/ResearchProjectPage.tsx` and focused frontend contract tests.
- No backend, database, or API changes.
