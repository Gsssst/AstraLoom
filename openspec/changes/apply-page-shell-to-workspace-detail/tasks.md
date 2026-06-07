## 1. Workspace Detail Shell Adoption

- [x] 1.1 Import and apply `PageShell` to `WorkspaceDetailPage`.
- [x] 1.2 Move back/module shortcuts into shell actions.
- [x] 1.3 Preserve dashboard cards, launchpad, resources, members, activity, and modals.

## 2. Error Recovery

- [x] 2.1 Use `getApiErrorDetails` for workspace load, candidates, member, resource bind, and unlink failures.
- [x] 2.2 Persist the latest workspace operation failure in a dismissible Alert with recovery, category, retryability, and status.
- [x] 2.3 Clear stale workspace failure feedback on successful operations where appropriate.

## 3. Tests And Verification

- [x] 3.1 Extend PageShell contract tests for workspace detail adoption and recovery guidance.
- [x] 3.2 Validate the OpenSpec change.
- [x] 3.3 Run targeted frontend tests and build.
