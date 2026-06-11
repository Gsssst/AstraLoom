## 1. Paper Chat Stream Reliability

- [x] 1.1 Add backend stream interruption event for late failures after visible content.
- [x] 1.2 Update paper detail stream consumer to mark interrupted turns without appending warning text to content.
- [x] 1.3 Preserve empty-answer fallback behavior.

## 2. Structured PDF Maintenance

- [x] 2.1 Add bounded admin maintenance endpoint for structured PDF batch parsing.
- [x] 2.2 Add maintenance recommendation/action for missing or failed structured parse metadata.
- [x] 2.3 Show structured parse readiness and batch action in the maintenance center UI.

## 3. Verification

- [x] 3.1 Add backend tests for late stream interruption and batch parse maintenance.
- [x] 3.2 Run OpenSpec validation, backend targeted tests, and frontend build.
- [x] 3.3 Commit the change.
