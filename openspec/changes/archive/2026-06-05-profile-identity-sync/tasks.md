## 1. Backend Recovery Contract

- [x] 1.1 Return persisted avatar and display name fields from `/api/auth/me`.
- [x] 1.2 Add a regression test for restoring visible profile identity from the current-user endpoint.

## 2. Frontend State Synchronization

- [x] 2.1 Add an authentication-store action for merging successful profile updates.
- [x] 2.2 Synchronize avatar, display-name, and email saves from settings into local and global user state.

## 3. Verification

- [x] 3.1 Run focused backend tests and the full backend test suite.
- [x] 3.2 Run the frontend production build and validate the OpenSpec change in strict mode.
