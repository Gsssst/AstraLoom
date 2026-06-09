## Overview

Reuse the existing `papers.importance_label` field and the current shared marker values: `important` and `interesting`. The feature is a search/filter improvement, not a new annotation model.

## Design

- Backend `GET /api/papers/search` accepts optional `importance_label`.
- Valid values are:
  - `important`
  - `interesting`
  - omitted / `all` for no marker filtering
- The filter applies only to local library results:
  - no-query local browse via SQL `WHERE papers.importance_label = ...`
  - query local search via the post-retrieval `paper_scores` filter path
- Remote search results remain unfiltered by shared markers because they are not persisted library papers.
- Frontend adds a compact Select in the local filter row.

## Boundaries

- This change does not add new marker labels.
- This change does not alter the shared marker update endpoint.
- This change does not filter saved/collection/reading-list endpoints unless those views later route through `/papers/search`.

## Verification

- Backend test covers local browse and keyword search filtering.
- Frontend contract test checks request parameter wiring and UI options.
- Frontend build and OpenSpec validation pass.
