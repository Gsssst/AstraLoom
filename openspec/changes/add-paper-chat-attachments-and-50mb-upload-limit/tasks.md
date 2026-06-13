## 1. Shared Attachment Workflow

- [x] 1.1 Extract reusable temporary chat attachment state and upload handling with a 50MB per-file limit.
- [x] 1.2 Move main chat upload handling to the shared workflow while preserving current PDF/image behavior.

## 2. Paper Detail Chat Attachments

- [x] 2.1 Add paper-detail AI Q&A attachment chips and upload control.
- [x] 2.2 Block paper-detail send while attachments are extracting.
- [x] 2.3 Include extracted PDF text and image attachment payloads in paper-detail ask-stream requests and displayed user messages.

## 3. Verification and Commit

- [x] 3.1 Add frontend contract tests for 50MB validation and paper-detail attachment support.
- [x] 3.2 Run OpenSpec validation, targeted frontend tests, and frontend build.
- [x] 3.3 Commit the implementation.
