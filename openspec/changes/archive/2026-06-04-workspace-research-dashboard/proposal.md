# Change: Workspace research dashboard

## Why

The workspace detail page now supports resources, members, permissions, and activity logs, but it still reads like a collection of lists. Users need an at-a-glance research dashboard that answers: what do we have, what is missing, what changed recently, and what should we do next?

## What Changes

- Add a dashboard summary to workspace detail data.
- Compute resource coverage, progress score, and actionable status cards.
- Rework the workspace detail page into a dashboard layout with KPI cards, progress guidance, resource sections, activity, and members.
- Keep existing resource binding and member management controls.

## Impact

- Workspace detail response gains `dashboard`.
- Workspace detail UI changes layout only; existing APIs remain unchanged.
