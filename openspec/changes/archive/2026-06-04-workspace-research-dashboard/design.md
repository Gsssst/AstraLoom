# Design: Workspace research dashboard

## Backend Dashboard Summary

Workspace detail includes:

- `progress_score`: 0-100 based on linked papers, research projects, writing projects, and recent activity.
- `stage`: coarse stage such as `setup`, `researching`, `drafting`, or `active`.
- `status_cards`: compact cards for papers, research projects, writing drafts, and activity.
- `resource_balance`: counts grouped by resource type.

## Frontend Layout

Workspace detail becomes:

- Hero summary with role/member context and quick navigation.
- KPI cards for linked papers, research projects, writing drafts, recent activities, and progress.
- Main left column for resource lists and binding.
- Right column for next actions, members, and activity timeline.

## Compatibility

Existing `summary`, `next_actions`, `activities`, and member data remain available.
