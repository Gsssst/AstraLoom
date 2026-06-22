## 1. OpenSpec Hygiene

- [x] 1.1 Create proposal, design, and spec deltas for reducing PDF zoom flashing.

## 2. Frontend Implementation

- [x] 2.1 Split PDF zoom into immediate display zoom and debounced render zoom.
- [x] 2.2 Apply transient CSS scale only while render zoom is catching up, then settle to high-resolution rendering.
- [x] 2.3 Reset and clean up zoom debounce state across PDF URL changes and unmount.

## 3. Verification

- [x] 3.1 Update PDF zoom contract tests for two-stage rendering.
- [x] 3.2 Run OpenSpec validation, targeted frontend tests, frontend build, and commit the change.
