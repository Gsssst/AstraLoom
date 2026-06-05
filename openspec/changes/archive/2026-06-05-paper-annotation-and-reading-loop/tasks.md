# Tasks

## 1. Backend

- [x] Add `personal_annotations` to `UserPaper` and create migration.
- [x] Add annotation request/response models.
- [x] Add list/create/delete annotation endpoints.
- [x] Add backend tests for annotation lifecycle and state preservation.

## 2. Frontend Paper Detail

- [x] Load saved annotations for the current paper.
- [x] Add save-annotation action for selected PDF quote.
- [x] Add saved annotation list with ask/delete actions.
- [x] Reuse existing paper chat stream when asking about an annotation.

## 3. Frontend Digest Center

- [x] Track local paper ids returned by one-click ingest.
- [x] Add digest actions for `加入待读` and `开始阅读`.
- [x] Make `稍后阅读` ingest and mark the paper as unread.
- [x] Show reading-loop state after an action succeeds.

## 4. Verification

- [x] Run backend tests.
- [x] Run frontend production build.
- [x] Run layout contract tests.
- [x] Attempt browser verification if available. Browser WebView attach timed out; covered with backend tests, build, and layout checks.
- [x] Run strict OpenSpec validation.
