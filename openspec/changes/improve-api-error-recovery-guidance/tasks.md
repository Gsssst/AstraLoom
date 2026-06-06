## 1. Structured Error Details

- [x] 1.1 Add shared API error detail types and helper functions while preserving existing message helpers.
- [x] 1.2 Classify timeout, network, auth, permission, validation, conflict, upstream, server, and unknown failures.

## 2. Settings Adoption

- [x] 2.1 Store API connection test failure details in settings state.
- [x] 2.2 Render persistent Alert feedback with severity, message, recovery suggestion, and retryability.
- [x] 2.3 Clear stale test feedback when saving or re-testing model config.

## 3. Tests And Verification

- [x] 3.1 Add API error helper tests for structured details.
- [x] 3.2 Add settings contract coverage for persistent API test failure feedback.
- [x] 3.3 Validate the OpenSpec change.
- [x] 3.4 Run targeted frontend tests and build.
