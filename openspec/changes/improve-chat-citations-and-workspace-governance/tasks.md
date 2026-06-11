## 1. Chat Retrieval References

- [x] 1.1 Add deterministic web result relevance scoring/filtering and metadata helpers.
- [x] 1.2 Apply filtering before web context injection and returned chat references.
- [x] 1.3 Update chat UI labels/tooltips so references are presented as retrieved sources with provider/query metadata.
- [x] 1.4 Add regression tests for unrelated fallback web results.

## 2. Admin Workspace Inspection

- [x] 2.1 Add admin-only workspace detail API that returns rich workspace content without requiring membership.
- [x] 2.2 Add admin console action to open workspace contents and show detail in an admin drawer/modal.
- [x] 2.3 Add tests that the new route is admin-only and returns resource/member/activity content.

## 3. Workspace Member Picker

- [x] 3.1 Add workspace member candidate search API for owners.
- [x] 3.2 Add service helper that lists active users with membership status and profile labels.
- [x] 3.3 Replace the add-member raw input with searchable Select candidates while preserving typed username/email submission.
- [x] 3.4 Add tests for candidate filtering and existing-member status.

## 4. Verification

- [x] 4.1 Validate the OpenSpec change.
- [x] 4.2 Run targeted backend tests.
- [x] 4.3 Run frontend build or type check.
- [x] 4.4 Report git status and the recommended git add/commit commands.
