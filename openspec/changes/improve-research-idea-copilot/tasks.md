## 1. Backend Copilot API

- [ ] 1.1 Add request/response schemas for Idea Copilot discussion modes and structured metadata.
- [ ] 1.2 Build a bounded Copilot context from idea fields, evidence/review metadata, validation, execution pack, lineage, evolution metadata, and recent discussion.
- [ ] 1.3 Update discussion handling to prompt by mode, parse structured replies, store metadata in `discussion_log`, and fall back safely for unstructured replies.
- [ ] 1.4 Add a discussion-driven evolution endpoint that reuses the existing Proposal evolution service.

## 2. Frontend Copilot Experience

- [ ] 2.1 Replace inline AI discussion with a focused Idea Copilot panel opened from Proposal cards.
- [ ] 2.2 Render markdown discussion, mode controls, context chips, quick prompts, structured risks/actions/questions, and send/evolve actions.
- [ ] 2.3 Refresh Proposal state after discussion-driven evolution and preserve existing validation/execution/lineage actions.

## 3. Verification

- [ ] 3.1 Add backend tests for mode validation, context-aware structured response shape, and discussion-driven evolution.
- [ ] 3.2 Add frontend contract tests for Copilot panel controls, markdown rendering, structured metadata, and evolution action.
- [ ] 3.3 Run strict OpenSpec validation plus focused backend/frontend tests and build checks.
