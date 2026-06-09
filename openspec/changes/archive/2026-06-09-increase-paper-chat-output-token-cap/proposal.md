## Why

Paper-detail AI Q&A is capped by the generic chat defaults, which are too small for long reasoning-heavy paper answers. The configured models support much larger output budgets, so the paper Q&A path should use provider-aware limits instead of the old shared 16K/32K defaults.

## What Changes

- Add provider/model-aware output token ceilings for LLM calls.
- Use a high paper-Q&A output budget for both streamed and non-streamed paper-detail chat.
- Cap DeepSeek V4 Pro paper Q&A at 384,000 output tokens.
- Cap the OpenAI-compatible GPT model paper Q&A at 128,000 output tokens.
- Keep fallback/retry behavior bounded by the active model's supported ceiling.

## Capabilities

### New Capabilities

### Modified Capabilities
- `paper-detail-chat-parity`: Paper-detail AI Q&A uses provider-aware long-output budgets rather than generic chat defaults.

## Impact

- `backend/app/services/llm.py`: model output limit policy and retry ceilings.
- `backend/app/api/papers.py`: paper-detail Q&A max token usage.
- Backend tests covering model-specific limits and paper Q&A routing.
