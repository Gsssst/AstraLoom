# Tasks

## 1. Backend

- [x] Add `read_status` to paper list response objects where applicable.
- [x] Add `/papers/collection/reading-status-counts`.
- [x] Tighten reading-list status validation and return `read_status`.
- [x] Return `saved: true` from read-status updates.
- [x] Add focused backend tests for counts and state preservation.

## 2. Frontend

- [x] Add reading status filter/count UI to the paper library.
- [x] Pass selected reading status to the reading-list API.
- [x] Add quick status actions on paper cards.
- [x] Add reading status control to the paper detail toolbar.
- [x] Keep refresh behavior localized and avoid page reloads.

## 3. Verification

- [x] Run backend tests.
- [x] Run frontend build and layout checks.
- [x] Run `openspec validate paper-reading-workflow --strict`.
- [x] Attempt browser verification on the paper library/detail pages. Browser WebView attach timed out; covered with frontend build/layout and backend tests.
