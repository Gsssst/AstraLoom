## 1. OpenSpec Validation

- [x] 1.1 Validate the OpenSpec change before implementation.

## 2. Backend Issue Workflow

- [x] 2.1 Add resource reference fields to issue create/update responses through issue metadata.
- [x] 2.2 Include recent open issue summaries in workspace list/detail responses.
- [x] 2.3 Add high-priority open workspace issues to workspace next actions and action center actions.
- [x] 2.4 Emit in-app notifications for issue creation, comments, close, and reopen events.
- [x] 2.5 Add open issue context and references to workspace AI assistant context.

## 3. Frontend Workspace and Resource UI

- [x] 3.1 Convert workspace detail into tabbed overview/issues/resources/assistant/activity sections without removing existing content.
- [x] 3.2 Support workspace issue deep links with `?issue=<id>` and show resource references in issue list/detail.
- [x] 3.3 Add reusable resource issue entry UI for paper detail, research project, and writing pages.
- [x] 3.4 Preserve existing workspace assistant, resource binding, member management, and issue workflows.

## 4. Frontend Search and Actions

- [x] 4.1 Add workspace issue results to the global command palette.
- [x] 4.2 Ensure action center can render high-priority workspace issue actions using existing action card patterns.

## 5. Tests

- [x] 5.1 Add backend tests for issue resource references, notifications, next actions, command/search payloads, and assistant issue context.
- [x] 5.2 Add frontend contract tests for workspace tabs, issue deep links, resource issue entry points, command palette issue search, and action rendering.

## 6. Verification

- [x] 6.1 Run OpenSpec strict validation after implementation.
- [x] 6.2 Run targeted backend tests.
- [x] 6.3 Run targeted frontend contract tests.
- [x] 6.4 Run frontend build.
- [x] 6.5 Run `git diff --check`.
