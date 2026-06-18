## 1. OpenSpec And Contracts

- [x] 1.1 Create proposal, design, spec deltas, and task list for paper chat collaboration sharing.
- [x] 1.2 Add backend contract coverage for share targets, permission rejection, notification creation, and workspace activity creation.
- [x] 1.3 Add frontend contract coverage for assistant answer share affordance and notification routing.

## 2. Backend Implementation

- [x] 2.1 Add paper share target and share request/response schemas.
- [x] 2.2 Implement `GET /papers/{paper_id}/share-targets` using linked workspace membership.
- [x] 2.3 Implement `POST /papers/{paper_id}/share-chat-insight` with bounded payloads, workspace activity, and recipient notifications.
- [x] 2.4 Ensure notification metadata includes source paper path and structured shared insight context.

## 3. Frontend Implementation

- [x] 3.1 Add share state, target loading, and submit handling to paper detail chat.
- [x] 3.2 Add a share-to-members action on completed assistant answer messages.
- [x] 3.3 Add a share modal with linked workspace selection, optional sender note, empty-state guidance, and success feedback.
- [x] 3.4 Route global `paper_chat_share` notifications back to the source paper.

## 4. Verification

- [x] 4.1 Run targeted backend/frontend contract tests.
- [x] 4.2 Run frontend build and OpenSpec validation.
- [x] 4.3 Review diff and commit the completed change.
