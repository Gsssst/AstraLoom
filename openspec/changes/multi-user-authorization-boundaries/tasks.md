## 1. Shared Authorization Dependencies

- [x] 1.1 Add a reusable administrator dependency layered on authenticated user lookup.

## 2. Private Resource Ownership

- [x] 2.1 Require authenticated ownership for research projects, ideas, experiments, and project share-link creation while preserving public token-based shared views.
- [x] 2.2 Require authenticated ownership for folder listing, nesting, and deletion.
- [x] 2.3 Prevent writing exports from including research ideas from a project the current user does not own.

## 3. Administrative Boundaries

- [x] 3.1 Restrict all-user usage summaries and dashboard data to administrators while limiting ordinary usage history to the current user.
- [x] 3.2 Restrict internal task APIs and global paper-library mutation endpoints to administrators.

## 4. Frontend Alignment

- [x] 4.1 Hide global paper-library mutation controls from ordinary users while preserving personal collection controls.
- [x] 4.2 Load all-user usage summaries in settings only for administrators.

## 5. Regression Verification

- [x] 5.1 Add focused backend regression tests for administrator checks, owner filters, protected routes, and usage history scoping.
- [x] 5.2 Run backend regression tests, compile checks, frontend production build, and local authorization smoke checks.
