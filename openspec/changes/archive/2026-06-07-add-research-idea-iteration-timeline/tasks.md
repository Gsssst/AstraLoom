## 1. Backend Timeline API

- [x] 1.1 Add response schema and endpoint for Proposal iteration timeline.
- [x] 1.2 Build derived events from idea creation, evolution metadata, validation, execution pack, Copilot discussion metadata, experiments, and child versions.
- [x] 1.3 Keep event ordering stable and payload bounded.

## 2. Frontend Timeline Experience

- [x] 2.1 Add timeline state and loading/error handling to the research project page.
- [x] 2.2 Add Proposal and Copilot actions that open a focused timeline drawer.
- [x] 2.3 Render categorized events with tags, severity, summaries, and details.

## 3. Verification

- [x] 3.1 Add backend tests for timeline event derivation, sparse Proposal fallback, and bounded discussion milestones.
- [x] 3.2 Add frontend contract tests for timeline endpoint use, drawer rendering, and error handling.
- [x] 3.3 Run strict OpenSpec validation plus focused backend/frontend tests and build checks.
