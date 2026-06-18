## Why

Paper AI reading shares are currently limited to a linked project space and a single assistant answer. Users need a more flexible collaboration flow: pick several useful turns from a paper reading conversation and push that curated context to any user in the system.

## What Changes

- Add a direct paper-chat sharing flow that can target arbitrary active users, independent of project-space membership.
- Let the sender select multiple chat messages from the current paper conversation before opening the share modal.
- Keep the existing one-click share action as a shortcut that preselects the assistant answer and its nearest prior user question.
- Store a bounded, structured message bundle in notification metadata so recipients can inspect the selected exchange and jump back to the source paper.
- Preserve backward compatibility for the existing workspace share payload where practical, but make direct user recipients the primary UI.

## Capabilities

### New Capabilities

- `paper-chat-directed-sharing`: Covers searching share recipients, selecting multiple paper-chat messages, and sending a structured paper-reading excerpt to arbitrary users.

### Modified Capabilities

- `notification-digest-center`: Paper chat share notifications carry selected-message bundles and route recipients back to the source paper.

## Impact

- Backend API: extend paper chat share endpoints with recipient-user search and multi-message share payloads.
- Backend models: reuse `Notification.metadata_json`; no new table is required for this slice.
- Frontend: paper detail AI chat gains a selectable share mode, message checkboxes, recipient search, and a multi-message preview modal.
- Tests: update backend and frontend contract tests for arbitrary recipients, selected messages, and notification metadata.
