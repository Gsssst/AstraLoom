## 1. Backend Progress Board

- [ ] 1.1 Add board response schemas and project board endpoint.
- [ ] 1.2 Derive per-Proposal status, priority, blockers, signals, and recommended action from existing validation/execution/experiment/discussion data.
- [ ] 1.3 Group board items by stable status and return summary counts.

## 2. Frontend Board Experience

- [ ] 2.1 Add board loading state and fetch project board data.
- [ ] 2.2 Add a Progress Board tab with grouped columns and Proposal cards.
- [ ] 2.3 Wire recommended actions to existing validation, execution pack, Copilot, experiment, writing, timeline, and evidence views.

## 3. Verification

- [ ] 3.1 Add backend tests for status classification, priority signals, empty board fallback, and grouping.
- [ ] 3.2 Add frontend contract tests for board endpoint use, grouped rendering, and recommended actions.
- [ ] 3.3 Run strict OpenSpec validation plus focused backend/frontend tests and build checks.
