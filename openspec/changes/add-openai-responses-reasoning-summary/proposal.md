## Why

The OpenAI-compatible GPT endpoint supports the OpenAI Responses API, which can stream official reasoning summaries for reasoning models. The app currently marks GPT-compatible models as not supporting thinking because the Chat Completions path does not expose DeepSeek-style `reasoning_content`.

## What Changes

- Add an OpenAI Responses API streaming path for the OpenAI-compatible provider when thinking display is requested.
- Map `response.reasoning_summary_text.delta` events to the app's existing `reasoning` stream events.
- Map `response.output_text.delta` events to the app's existing `content` stream events.
- Keep DeepSeek on the existing Chat Completions reasoning path.
- Clearly treat GPT reasoning output as a summary, not raw chain-of-thought.

## Capabilities

### New Capabilities
- `openai-responses-reasoning-summary`: GPT-compatible models can display Responses API reasoning summaries when supported by the configured endpoint.

### Modified Capabilities

## Impact

- OpenAI-compatible LLM streaming in `backend/app/services/llm.py`.
- Chat stream provider routing in `backend/app/api/chat_sessions.py`.
- Chat model capability metadata and tests.
