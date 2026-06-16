## Why

Stage 2 needs chat tools that create research artifacts instead of only answering text. A bounded `generate_image` tool lets chat produce method-diagram drafts, paper figure concepts, and group-meeting illustrations while keeping the provider integration isolated and observable.

## What Changes

- Add a backend image generation service with a provider abstraction for OpenAI-compatible image APIs.
- Register a read-only `generate_image` chat tool with prompt, purpose, style, size, and output count arguments.
- Return generated image artifacts as data URLs plus metadata so the existing tool trace can expose the result.
- Reject generation clearly when the image provider is not configured.
- Add deterministic fallback routing for explicit image-generation prompts.
- Keep this slice storage-free: generated images are returned in the tool observation and are not persisted to the library or filesystem.

## Capabilities

### New Capabilities

- `chat-image-generation-tool`: Chat can generate bounded image artifacts through a registered tool.

### Modified Capabilities

- `chat-agent-tool-runtime`: The registered tool set expands with read-only `generate_image`.

## Impact

- Backend config for image generation provider/model.
- Backend service under `backend/app/services/`.
- Chat tool registry in `backend/app/services/chat_agent_tools.py`.
- Focused backend tests for provider payloads, missing configuration, tool schema, observations, and deterministic routing.
