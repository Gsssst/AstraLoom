## 1. Backend Tool Mode

- [x] 1.1 Add validated `tool_mode` to chat send requests with values `auto`, `off`, and `force`.
- [x] 1.2 Update chat planner gating so `off` skips generic planner/tool fallback while Research Scout remains independent.
- [x] 1.3 Add force-mode behavior so planner no-action or invalid-output cases attempt deterministic fallback when available.
- [x] 1.4 Include selected tool mode and force fallback usage in planner trace metadata.

## 2. Frontend Control

- [x] 2.1 Add chat composer state and compact control for automatic, disabled, and forced tool behavior.
- [x] 2.2 Submit `tool_mode` in both normal text and attachment-backed stream requests.
- [x] 2.3 Update composer runtime label so users can see whether generic tools are automatic, disabled, or forced.
- [x] 2.4 Keep Research Scout mode behavior and copy independent from generic tool mode.

## 3. Verification

- [x] 3.1 Add backend tests for `tool_mode` validation, `off` gating, `auto` behavior, `force` fallback, and Research Scout isolation.
- [x] 3.2 Add planner tests for forced deterministic fallback when the model returns no actions.
- [x] 3.3 Update frontend contract tests for tool mode control and payload submission.
- [x] 3.4 Run OpenSpec validation, focused backend tests, frontend contract tests, and frontend build.
