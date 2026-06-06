## Why

After candidate generation completes, the Top Proposal tab shows rich review data but still behaves like a flat list. Users need a faster way to identify the strongest proposals, separate pinned/rejected items, and make decisions without opening every panel.

## What Changes

- Add proposal sorting by review score, novelty, feasibility, evidence count, and recency.
- Add status filtering for all, pending, pinned, rejected, and implemented proposals.
- Highlight the current recommended proposal using existing review and status data.
- Surface proposal counts and primary decision actions near the proposal list.
- Keep existing proposal detail, discussion, validation, comparison, and writing actions intact.

## Capabilities

### New Capabilities

### Modified Capabilities
- `research-idea-workbench`: The Top Proposal interface should support ranked review and decision-oriented filtering.

## Impact

- Frontend proposal tab behavior in `frontend/src/pages/ResearchProjectPage.tsx`.
- Frontend contract coverage for proposal ranking/filtering controls.
- OpenSpec requirements for the research idea workbench interface.
