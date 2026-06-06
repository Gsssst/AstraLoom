## 1. Stream Cancellation

- [x] 1.1 Add `AbortController` lifecycle state for streamed chat sends.
- [x] 1.2 Add a stop-generation handler that aborts the active stream and resets local sending state.
- [x] 1.3 Ensure cancellation does not append a generic assistant error.

## 2. UI

- [x] 2.1 Add a stop button to the active stream status row and composer send area.
- [x] 2.2 Style the stop control consistently with the chat composer/status UI.
- [x] 2.3 Add a frontend contract test for stream cancellation wiring.

## 3. Verification

- [x] 3.1 Validate the OpenSpec change.
- [x] 3.2 Run frontend contract test and frontend build.
- [x] 3.3 Commit the focused implementation.
