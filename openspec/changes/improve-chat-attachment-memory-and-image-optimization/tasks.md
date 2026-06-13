## 1. Shared Attachment State

- [x] 1.1 Extend the shared attachment hook with remembered attachment state, removal, clear, and merged ready attachment helpers.
- [x] 1.2 Move successfully sent ready attachments into remembered state for main chat and paper-detail chat.
- [x] 1.3 Include remembered attachment text and images in follow-up requests for main chat and paper-detail chat.

## 2. Image Payload Optimization

- [x] 2.1 Add browser-side image resize/re-encode utilities inside the shared attachment workflow.
- [x] 2.2 Store optimized data URL metadata and fallback status on image attachments.
- [x] 2.3 Use optimized image payloads for model requests while preserving original filename and MIME type.

## 3. User Interface

- [x] 3.1 Render remembered attachment chips separately from current-turn chips in main chat and paper-detail chat.
- [x] 3.2 Show concise extraction, remembered, optimized, and fallback status in attachment chips.

## 4. Verification and Commit

- [x] 4.1 Add frontend contract tests for remembered attachments and image optimization.
- [x] 4.2 Run OpenSpec validation, targeted frontend tests, and frontend build.
- [x] 4.3 Commit the implementation.
