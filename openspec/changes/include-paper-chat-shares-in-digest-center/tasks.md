## 1. OpenSpec And Contracts

- [x] 1.1 Create proposal, design, specs, and task list.
- [x] 1.2 Update backend notification contract coverage for mixed paper push categories.
- [x] 1.3 Update frontend contract coverage for paper chat share cards in the push center.

## 2. Backend Implementation

- [x] 2.1 Expand `/notifications/digests` to include `paper_chat_share`.
- [x] 2.2 Expand digest unread count and mark-all-read to include `paper_chat_share`.
- [x] 2.3 Keep digest paper feedback endpoint scoped to category `digest`.

## 3. Frontend Implementation

- [x] 3.1 Add paper chat share metadata types to `PaperDigestInboxPage`.
- [x] 3.2 Render paper chat share cards with selected messages and open-paper action.
- [x] 3.3 Update center labels/counts from digest-only to paper-push wording.

## 4. Verification

- [x] 4.1 Run targeted backend/frontend tests.
- [x] 4.2 Run OpenSpec validation and frontend build.
- [x] 4.3 Review diff and commit.
