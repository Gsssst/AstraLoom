## 1. Backend Timeline API

- [ ] 1.1 Add response schema and endpoint for Proposal iteration timeline.
- [ ] 1.2 Build derived events from idea creation, evolution metadata, validation, execution pack, Copilot discussion metadata, experiments, and child versions.
- [ ] 1.3 Keep event ordering stable and payload bounded.

## 2. Frontend Timeline Experience

- [ ] 2.1 Add timeline state and loading/error handling to the research project page.
- [ ] 2.2 Add Proposal and Copilot actions that open a focused timeline drawer.
- [ ] 2.3 Render categorized events with tags, severity, summaries, and details.

## 3. Verification

- [ ] 3.1 Add backend tests for timeline event derivation, sparse Proposal fallback, and bounded discussion milestones.
- [ ] 3.2 Add frontend contract tests for timeline endpoint use, drawer rendering, and error handling.
- [ ] 3.3 Run strict OpenSpec validation plus focused backend/frontend tests and build checks.
