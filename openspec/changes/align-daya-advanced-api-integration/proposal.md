## Why

The current chat tool integrations were added before the Daya advanced API documents were reviewed in detail. Image generation currently assumes an OpenAI `/images/generations` endpoint, while Daya documents image generation through its Vertex/Gemini-compatible `generateContent` API, and model-planned tools can benefit from Daya's Chat Completions `response_format` structured output support.

## What Changes

- Adapt the chat `generate_image` backend service to Daya's Vertex/Gemini-compatible image generation contract while reusing the existing Daya API key.
- Keep generated image artifacts storage-free and return data URLs parsed from Vertex/Gemini response parts.
- Add a direct OpenAI-compatible Chat Completions helper for Daya extension parameters such as `response_format` and `web_search_options`.
- Use structured output for the LLM tool planner when the active provider is OpenAI-compatible, reducing malformed tool-plan JSON.
- Preserve existing LiteLLM paths for ordinary chat and existing Responses API streaming behavior.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `chat-image-generation-tool`: The image generation service must support Daya Vertex/Gemini-compatible image generation payloads and response parsing.
- `llm-tool-planner`: The planner should use provider-supported structured JSON output when available.

## Impact

- Affected backend code: `backend/app/services/image_generation.py`, `backend/app/services/llm.py`, `backend/app/services/chat_tool_planner.py`.
- Affected configuration: image generation model/base settings and `.env.example` documentation.
- Affected tests: image generation, LLM service, and planner tests.
- No database migrations or new external runtime dependencies are expected.
