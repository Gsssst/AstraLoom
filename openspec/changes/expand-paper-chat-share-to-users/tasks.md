## 1. OpenSpec And Contracts

- [x] 1.1 Create proposal, design, spec deltas, and tasks for direct user multi-message paper chat sharing.
- [x] 1.2 Update backend contract coverage for arbitrary user recipients, selected-message bounding, and invalid recipient rejection.
- [x] 1.3 Update frontend contract coverage for selection mode, recipient search, multi-message preview, and notification routing.

## 2. Backend Implementation

- [x] 2.1 Add paper chat share recipient and selected-message schemas.
- [x] 2.2 Implement `GET /papers/{paper_id}/share-recipients` using active user search independent of project spaces.
- [x] 2.3 Extend `POST /papers/{paper_id}/share-chat-insight` to accept `recipient_user_ids` and `selected_messages`.
- [x] 2.4 Preserve the existing workspace share compatibility path and keep payloads bounded.

## 3. Frontend Implementation

- [x] 3.1 Add paper chat share-selection state and selected-message helpers.
- [x] 3.2 Add a compact "选择推送" mode with message checkboxes and selected-count controls.
- [x] 3.3 Replace the modal target selector with searchable user recipients and selected-message preview.
- [x] 3.4 Keep the assistant shortcut by preselecting the paired question and answer.

## 4. Verification

- [x] 4.1 Run targeted backend and frontend contract tests.
- [x] 4.2 Run OpenSpec validation and frontend build or targeted type/build check.
- [x] 4.3 Review diff and commit the completed change.
