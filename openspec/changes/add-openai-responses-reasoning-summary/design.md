## Context

DeepSeek returns `reasoning_content` through the current Chat Completions-compatible stream, which the app already renders as a collapsible thinking panel. OpenAI Responses API uses a different streaming schema: normal answer deltas arrive as `response.output_text.delta`, while reasoning summary deltas arrive as `response.reasoning_summary_text.delta`.

The configured GPT endpoint is reported to support the OpenAI Responses API, so the app can request reasoning summaries when the user has enabled thinking display.

## Goals / Non-Goals

**Goals:**
- Stream GPT reasoning summaries into the existing thinking panel.
- Preserve normal GPT Chat Completions behavior when thinking display is off.
- Avoid exposing raw chain-of-thought claims in UI labels or code comments.
- Keep DeepSeek behavior unchanged.

**Non-Goals:**
- Switch all GPT calls to Responses API.
- Add non-streaming Responses API support.
- Support tool calls or multi-output item rendering from Responses API.
- Store reasoning summaries separately from existing message reasoning fields.

## Decisions

- Use `httpx.AsyncClient` directly for the Responses API streaming request.
  - Rationale: LiteLLM support for Responses reasoning summary events can vary by version, while the endpoint is OpenAI-compatible and the event mapping is small.

- Build the Responses `input` payload from existing chat messages.
  - Rationale: Responses API accepts role/content inputs and the app's text and multimodal messages already follow OpenAI-style message shapes.

- Enable the Responses path only when active provider is OpenAI-compatible and `show_thinking` is true.
  - Rationale: normal GPT messages should keep the currently working Chat Completions path.

- Return summary deltas as `{"type": "reasoning"}`.
  - Rationale: the frontend already renders this stream type through `ThinkingPanel`.

## Risks / Trade-offs

- Some "OpenAI-compatible" endpoints may implement Chat Completions but only partially implement Responses streaming -> mitigation: surface API errors through the existing stream error path.
- Reasoning summaries may increase latency and cost -> mitigation: use the path only when the user enables thinking display.
- Summary event names may differ across providers -> mitigation: parse the documented OpenAI event names and ignore unknown events.
