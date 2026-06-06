## 1. Backend Run Cancellation

- [x] 1.1 Add a service/API helper that marks running idea workbench runs as `cancelled` while preserving latest stage, progress, and artifacts.
- [x] 1.2 Add an authenticated cancel endpoint for project-owned idea runs.
- [x] 1.3 Update the stream endpoint cleanup path to cancel its in-process task and persist a cancelled run when the browser aborts.

## 2. Frontend Generation Controls

- [x] 2.1 Add `AbortController` lifecycle handling to research idea run streaming.
- [x] 2.2 Add stop/retry/restart controls and clearer status labels to the workbench progress card.
- [x] 2.3 Highlight completed proposal generation with a next action to inspect Top Proposal results.

## 3. Tests And Verification

- [x] 3.1 Add backend tests for run cancellation and idempotent terminal-run cancellation.
- [x] 3.2 Add frontend contract coverage for stop, retry, restart, and completion next-action UI.
- [x] 3.3 Validate the OpenSpec change.
- [x] 3.4 Run targeted backend/frontend tests and frontend build.
