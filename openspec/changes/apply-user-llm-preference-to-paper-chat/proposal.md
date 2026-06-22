## Why

Users can save a personal LLM preference in Settings, but paper-detail AI Q&A still uses the server default model because the paper ask endpoints do not bind the authenticated user preference into the LLM request context.

This causes confusing behavior: Settings shows GPT/OpenAI-compatible as the user's selected model, while paper chat responses still identify as DeepSeek.

## What Changes

- Require the authenticated user on paper ask and paper ask-stream endpoints.
- Set request-scoped LLM preference from the current user before building/generating paper answers.
- Keep existing paper access, retrieval, streaming, evidence, and attachment behavior unchanged.
- Add backend contract coverage so paper Q&A endpoints cannot regress to provider-default model selection.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `paper-detail-chat-parity`: Paper-detail AI Q&A honors the current user's saved LLM provider/model preference.

## Impact

- Backend paper ask and ask-stream endpoints.
- Backend contract tests for user-scoped LLM preference propagation.
