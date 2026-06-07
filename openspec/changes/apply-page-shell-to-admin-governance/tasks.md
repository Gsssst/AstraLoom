## 1. Admin Shell Adoption

- [x] 1.1 Import and apply `PageShell` to `AdminPage`.
- [x] 1.2 Move refresh into shell actions and remove the local gradient hero.
- [x] 1.3 Preserve non-admin warning, metrics, tables, filters, and activity timeline.

## 2. Error Recovery

- [x] 2.1 Use `getApiErrorDetails` for admin data loading and user update failures.
- [x] 2.2 Persist the latest admin operation failure in a dismissible Alert with recovery, category, retryability, and status.
- [x] 2.3 Clear stale admin failure feedback on successful operations.

## 3. Tests And Verification

- [x] 3.1 Extend PageShell contract tests for Admin adoption and recovery guidance.
- [x] 3.2 Validate the OpenSpec change.
- [x] 3.3 Run targeted frontend tests and build.
