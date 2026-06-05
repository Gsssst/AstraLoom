## Overview

This change is primarily a workflow consolidation. The backend already exposes the required primitives:

- `/papers/maintenance/health`
- `/papers/maintenance/recommendations`
- `/papers/maintenance/search-diagnostics`
- `/papers/maintenance/rebuild-bm25`
- `/papers/maintenance/backfill-embeddings`
- `/papers/maintenance/backfill-full-text`
- `/folders/` with per-folder diagnostics

The paper library page will add a first-class maintenance center without moving or removing the settings-page implementation.

## Frontend

Extend `PapersPage.tsx` with:

- a new source/view option: `maintenance`;
- maintenance state: health, recommendations, diagnostics, query, loading/action states;
- admin-only API calls for global maintenance data;
- a maintenance view rendered in the scrollable content area;
- collection readiness cards derived from `collections[].diagnostics`.

When `source === "maintenance"`:

- the search bar becomes secondary;
- the paper list is replaced by a dashboard;
- admins can execute repair actions;
- non-admin users see an explanatory permission notice.

## Testing

Add/extend frontend source contract tests to assert the paper library exposes:

- the maintenance view label;
- health/recommendation/diagnostic endpoints;
- repair action endpoints;
- collection readiness warnings.

No backend tests are required unless backend APIs change.
