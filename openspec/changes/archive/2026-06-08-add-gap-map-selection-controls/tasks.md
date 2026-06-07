## 1. Backend Run Lifecycle

- [x] 1.1 Add Gap Map preview execution that stops in `gap_review` after evidence and gap extraction.
- [x] 1.2 Add continuation execution that applies selected gaps and generation constraints before candidate generation.
- [x] 1.3 Add owner-scoped API endpoints for Gap Map preview and continuation.

## 2. Backend Constraint Binding

- [x] 2.1 Filter and annotate Gap Map from selected/blocked gaps and focus notes.
- [x] 2.2 Include research mode, risk appetite, and resource budget in candidate and tree evolution prompts.
- [x] 2.3 Persist gap-selection metadata in run summaries and selected Idea review metadata.

## 3. Frontend Workbench Controls

- [x] 3.1 Add Gap Map preview and continue actions to the research project workbench.
- [x] 3.2 Add compact controls for selected gaps, focus note, research mode, risk appetite, and resource budget.
- [x] 3.3 Display applied gap-selection metadata in Proposal details.

## 4. Verification

- [x] 4.1 Add backend tests for preview stopping, continuation constraints, and selected Idea metadata.
- [x] 4.2 Add frontend contract tests for Gap Map selection controls and applied metadata display.
- [x] 4.3 Run targeted backend tests, frontend contract tests, frontend build, and OpenSpec validation.
