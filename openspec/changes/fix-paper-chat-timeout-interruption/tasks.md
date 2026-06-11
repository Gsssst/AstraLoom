## 1. Paper Chat Timeout Fix

- [x] 1.1 Replace the thinking-mode whole-stream timeout with a first-visible-content guard.
- [x] 1.2 Preserve recovery behavior when the primary thinking stream only emits reasoning or stalls before content.
- [x] 1.3 Preserve late interruption warnings for real exceptions after visible content starts.

## 2. Verification

- [x] 2.1 Add regression tests for slow thinking-mode answers that continue past the first-answer guard.
- [x] 2.2 Run OpenSpec validation and targeted backend tests.
- [x] 2.3 Commit the change.
