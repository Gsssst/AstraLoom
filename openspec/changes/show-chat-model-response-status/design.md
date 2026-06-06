## Context

The streaming chat endpoint already emits `status`, `meta`, `reasoning`, `content`, `error`, and `done` events. The current `meta` event only contains references, so the frontend cannot tell users which configured model is active or whether a slow response is still waiting for its first content token.

Similar chat products such as Open WebUI, Dify, and NextChat treat model identity and streaming progress as visible chat surface state. This project needs the same transparency because GPT-compatible endpoints may have materially different latency from DeepSeek.

## Goals / Non-Goals

**Goals:**
- Show the active provider/model label in the chat toolbar.
- Show compact capability indicators for knowledge base, web search, thinking, and image vision.
- Distinguish waiting for first token from active streaming, with elapsed time.
- Keep stream metadata safe for frontend consumption.

**Non-Goals:**
- Change model selection behavior in Settings.
- Add cancellation, retries, or queueing.
- Benchmark or tune provider latency.

## Decisions

- Extend the existing stream `meta` event instead of adding another endpoint.
  - Rationale: the frontend already consumes stream metadata during the exact turn that needs this state.

- Emit only display-safe model metadata.
  - Rationale: chat UI needs provider/model/capability flags, not API secrets or base URLs.

- Track timing in the frontend from send start and first streamed content/reasoning token.
  - Rationale: browser timing represents the user-visible wait and works across providers.

- Keep the UI compact in the existing toolbar and sending row.
  - Rationale: this is a working chat surface, not a settings page or debug console.

## Risks / Trade-offs

- The initial toolbar may not know the model until the first streamed response arrives -> mitigation: show a neutral placeholder until stream metadata is received.
- Capability flags are provider-level heuristics -> mitigation: label them as capabilities of the selected project provider, not guaranteed endpoint behavior.
