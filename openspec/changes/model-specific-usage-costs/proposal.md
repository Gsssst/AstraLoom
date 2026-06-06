## Why

Token usage cost estimates currently apply DeepSeek pricing to every model. After adding an OpenAI-compatible GPT model, the settings usage page can show misleading cost totals because GPT and DeepSeek have different input/output rates.

## What Changes

- Calculate usage cost from a model-specific pricing table instead of one fixed DeepSeek rate.
- Keep separate input-token and output-token prices.
- Allow deployment-specific price overrides through environment variables.
- Preserve existing usage records and API response shape.

## Capabilities

### New Capabilities

### Modified Capabilities
- `usage-attribution-and-digest-schedule`: Token usage cost estimates must use the recorded model's configured price.

## Impact

- Backend usage cost calculation in `backend/app/services/usage_tracker.py`.
- Environment settings and examples for DeepSeek and OpenAI-compatible token prices.
- Backend regression tests for per-model cost estimates.
