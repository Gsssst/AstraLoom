## 1. Parser Configuration

- [x] 1.1 Add advanced PDF parser settings with safe defaults.
- [x] 1.2 Forward parser settings through Docker Compose backend and worker environments.

## 2. Parser Backend

- [x] 2.1 Add parser subprocess environment helper with HuggingFace mirror/cache propagation.
- [x] 2.2 Normalize advanced parser JSON payloads into structured PDF blocks.
- [x] 2.3 Add command backend execution with timeout, output cap, and lightweight fallback.

## 3. Verification

- [x] 3.1 Add unit tests for payload normalization and parser environment propagation.
- [x] 3.2 Add command backend tests for success and fallback behavior.
- [x] 3.3 Run OpenSpec validation and targeted backend tests.
- [x] 3.4 Commit the change.
