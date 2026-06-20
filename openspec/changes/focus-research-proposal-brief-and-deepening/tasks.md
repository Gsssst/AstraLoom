## 1. Backend Brief Normalization

- [x] 1.1 Add `idea_brief` normalization helpers in `ResearchIdeaWorkbenchService`.
- [x] 1.2 Update candidate generation prompt/normalization to request and produce `idea_brief`.
- [x] 1.3 Persist `review_json.idea_brief` for selected proposals while preserving existing metadata.
- [x] 1.4 Add backend tests for brief normalization and persistence.

## 2. Backend Deepening Workflow

- [x] 2.1 Add evidence facet extraction for selected proposals.
- [x] 2.2 Add service method to deepen one selected proposal with optional focus and deterministic fallback.
- [x] 2.3 Add authenticated API endpoint `POST /api/research/ideas/{idea_id}/deepen`.
- [x] 2.4 Add backend tests for deepening success/fallback metadata updates.

## 3. Frontend Proposal Detail Simplification

- [x] 3.1 Add frontend types for `idea_brief` and `deepening` metadata.
- [x] 3.2 Render the compact Idea Brief first, preferring deepened brief when present.
- [x] 3.3 Collapse secondary review/evidence/execution details by default.
- [x] 3.4 Add a "深入打磨" action that calls the new endpoint and refreshes the selected proposal.
- [x] 3.5 Add/update frontend contract tests.

## 4. Verification

- [x] 4.1 Run backend focused tests.
- [x] 4.2 Run frontend contract tests.
- [x] 4.3 Run `openspec validate focus-research-proposal-brief-and-deepening --strict`.
- [x] 4.4 Run frontend build.
