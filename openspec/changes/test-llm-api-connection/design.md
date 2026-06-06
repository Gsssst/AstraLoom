## Context

The settings API tab already lists model options and allows admins to switch the active provider/model. The backend `LLMService` has enough information to make a small chat completion call using server-side environment variables, and usage tracking already records model usage.

## Goals / Non-Goals

**Goals:**
- Let an admin test the currently active provider/model from Settings.
- Report elapsed time in milliseconds.
- Return a short response preview for human confirmation.
- Keep API keys and base URL secrets server-side.

**Non-Goals:**
- Benchmark streaming first-token latency.
- Let users test arbitrary ad hoc keys from the browser.
- Add provider-specific health checks beyond one small Chat Completions request.

## Decisions

- Add `POST /settings/api-config/test`.
  - Rationale: the test belongs next to the current API configuration and can reuse admin authorization.

- Use a short Chinese prompt and low token budget.
  - Rationale: the test should validate end-to-end completion without wasting tokens.

- Measure elapsed time in the settings API route.
  - Rationale: it captures the server-side call duration that users care about when diagnosing provider speed.

- Return provider, model, configured, latency, and preview only.
  - Rationale: this is enough for UI feedback and avoids exposing credentials.

## Risks / Trade-offs

- The test consumes a small amount of model quota -> mitigation: use a minimal prompt and `max_tokens` budget.
- A successful test does not guarantee future long chats will be fast -> mitigation: label the result as a connection test, not a benchmark.
