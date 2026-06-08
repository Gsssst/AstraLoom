## 1. Backend Review And Revision Services

- [x] 1.1 Add service helper to build and normalize structured proposal review packages with deterministic fallback.
- [x] 1.2 Add owner-scoped API endpoint to create or refresh a proposal review package.
- [x] 1.3 Add owner-scoped API endpoint to create a child proposal from review guidance and annotate revision provenance.

## 2. Version Comparison And Board Signals

- [x] 2.1 Add deterministic parent-child proposal version comparison service/API.
- [x] 2.2 Add review-package and revision events to iteration timeline output.
- [x] 2.3 Extend proposal board classification and recommended actions for review blockers and revised children.

## 3. Frontend Revision Workflow

- [x] 3.1 Add proposal review package panel with objections, required experiments, revision plan, readiness, and refresh action.
- [x] 3.2 Add review-guided revision action and modal/focus input that creates a child Proposal and refreshes project state.
- [x] 3.3 Add version comparison view for revised Proposals and connect board actions to review/revision workflows.

## 4. Verification

- [x] 4.1 Add backend tests for review package fallback/persistence, review-guided child evolution, version comparison, timeline event, and board grouping.
- [x] 4.2 Add frontend contract tests for review package UI, revision endpoint usage, version comparison view, and board action routing.
- [x] 4.3 Run targeted backend tests, frontend contract tests, frontend build, and OpenSpec validation.
