## Context

`UsageTracker.log_usage()` stores prompt tokens, completion tokens, total tokens, model, and `cost_estimate`. It currently computes `cost_estimate` with DeepSeek-only CNY rates. The application now records multiple model names, including `deepseek-v4-pro` and `gpt-5.5`, so the cost estimator needs to choose a rate by model.

## Goals / Non-Goals

**Goals:**
- Use the recorded model name when estimating cost.
- Keep input and output token rates separate.
- Make rates configurable without database migrations.
- Keep the frontend/API response shape unchanged.

**Non-Goals:**
- Recalculate historical records automatically.
- Implement provider billing reconciliation.
- Add a new settings UI for editing rates.

## Decisions

- Store rates in application settings as CNY per 1M tokens.
  - Rationale: the UI already labels cost in CNY and converts to USD for display.
  - Alternative considered: USD canonical storage. That would require changing frontend semantics and existing labels.

- Match model names with normalized substring patterns.
  - Rationale: LiteLLM/provider model names can include prefixes such as `openai/`; substring matching covers `gpt-5.5`, `openai/gpt-5.5`, and DeepSeek aliases without schema changes.
  - Alternative considered: adding provider to `token_usage`. Useful later, but not required to estimate cost from the existing `model` column.

- Allow environment overrides for DeepSeek and OpenAI-compatible rates.
  - Rationale: third-party OpenAI-compatible providers can charge different rates from official vendors, so deployments need to set exact prices locally.

## Risks / Trade-offs

- Existing records keep their old stored `cost_estimate` -> mitigation: new calls are correct; historical backfill can be a separate maintenance task if needed.
- Unknown model names can still appear -> mitigation: fall back to the DeepSeek default rate and keep logging functional.
