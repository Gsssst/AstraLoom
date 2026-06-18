## Why

Paper AI reading currently helps one user understand a paper, but useful AI answers stay trapped inside that user's paper detail chat history. Research groups need a lightweight way to turn a useful AI reading exchange into shared project context without copying text into external chat tools.

## What Changes

- Add a paper-chat collaboration share flow that lets an authenticated user push one AI answer, its paired question, paper metadata, and evidence references to members of a linked project space.
- Reuse project spaces as the collaboration boundary, following the shared-library/private-group model used by mature research tools.
- Reuse in-app notifications so recipients see the shared reading insight in the global notification popover and can jump back to the source paper.
- Record a workspace activity entry for the shared AI reading insight so the project space has a durable collaboration trail.
- Keep this MVP narrow: sharing is a curated action from paper detail, not a general-purpose team chat system.

## Capabilities

### New Capabilities
- `paper-chat-collaboration-share`: Covers selecting a paper AI answer, choosing a linked workspace, and broadcasting a structured reading insight card to workspace members.

### Modified Capabilities
- `notification-digest-center`: Global notifications route paper chat collaboration share events and expose the new category.
- `workspace-resource-activity-log`: Workspace activity records shared paper AI insights as project-space activity.

## Impact

- Backend API: new paper endpoint for listing share targets and creating a share notification.
- Backend services/models: reuse `ProjectSpace`, `ProjectSpaceResource`, `ProjectSpaceActivity`, and `Notification`; no new table is required for the MVP.
- Frontend: paper detail AI answer cards gain a share action and modal; global notification routing recognizes the collaboration category.
- Tests: backend contract tests for permission/notification behavior and frontend contract tests for visible share affordances.
