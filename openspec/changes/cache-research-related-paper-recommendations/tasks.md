## 1. Backend Recommendation Cache

- [x] 1.1 Add deterministic cache-key helpers for research related-paper recommendations.
- [x] 1.2 Update the recommended-papers endpoint to return cached results by default and recompute on `refresh=true`.
- [x] 1.3 Persist refreshed recommendation results in project metadata.

## 2. Frontend Related-Papers Panel

- [x] 2.1 Update `ResearchProjectPage` to read recommendation response metadata.
- [x] 2.2 Add a manual refresh action and cached-state indicator to the related-papers card.

## 3. Tests And Verification

- [x] 3.1 Add backend tests for cached and refreshed recommendation behavior.
- [x] 3.2 Update frontend contract tests for cache metadata and refresh controls.
- [x] 3.3 Validate the OpenSpec change.
- [x] 3.4 Run targeted backend/frontend tests and frontend build.
