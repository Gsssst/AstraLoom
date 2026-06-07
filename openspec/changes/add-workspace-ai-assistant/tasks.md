## 1. OpenSpec Validation

- [x] 1.1 Validate the OpenSpec change before implementation.

## 2. Backend Assistant Flow

- [ ] 2.1 Add workspace assistant request/response schemas and endpoints under `/workspaces/{space_id}/assistant`.
- [ ] 2.2 Implement workspace membership checks for assistant state and send operations.
- [ ] 2.3 Reuse `ChatSession` and `ChatMessage` with workspace-scoped `metadata_json` filters.
- [ ] 2.4 Add workspace context assembly with linked resources, dashboard state, next actions, and recent activity references.
- [ ] 2.5 Send assistant prompts through the existing LLM service and persist user/assistant messages.
- [ ] 2.6 Exclude workspace-scoped assistant sessions from generic chat session listing.

## 3. Frontend Workspace Assistant UI

- [ ] 3.1 Add workspace assistant state, loading, sending, input, and error handling to `WorkspaceDetailPage`.
- [ ] 3.2 Render an AI assistant panel with quick prompts, message history, input, and send action.
- [ ] 3.3 Render workspace resource references returned by assistant replies.
- [ ] 3.4 Ensure failed sends keep the user's current input and show actionable feedback.

## 4. Tests

- [ ] 4.1 Add backend contract tests for workspace assistant routes, metadata scoping, context assembly, and generic chat exclusion.
- [ ] 4.2 Add frontend contract tests for workspace assistant panel, quick prompts, send flow, references, and error handling.

## 5. Verification

- [ ] 5.1 Run OpenSpec strict validation after implementation.
- [ ] 5.2 Run targeted backend tests.
- [ ] 5.3 Run targeted frontend contract tests.
- [ ] 5.4 Run frontend build.
- [ ] 5.5 Run `git diff --check`.
