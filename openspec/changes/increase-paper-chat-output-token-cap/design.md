## Overview

The change keeps the existing LLM API surface but adds explicit helper methods on `LLMService` for active-provider output budgets. Paper-detail Q&A will call these helpers instead of relying on the generic defaults.

## Design

- Keep conservative generic defaults for general chat call sites.
- Introduce provider-specific ceilings:
  - DeepSeek provider: `384000`
  - OpenAI-compatible provider: `128000`
  - Unknown providers: existing bounded default ceiling
- Add a paper-Q&A budget helper so paper chat does not duplicate provider checks.
- Update retry escalation to clamp at the active model ceiling instead of the old global `65536`.
- Pass the paper-Q&A budget explicitly to:
  - streamed paper Q&A without thinking
  - streamed paper Q&A with thinking
  - recovery stream
  - non-streamed paper Q&A

## Risks

- Very large outputs can be slower and more expensive. This is acceptable for paper-detail Q&A because the user explicitly expects long reasoning and long-form answers.
- Some compatible endpoints may advertise a model name but enforce a lower server-side limit. In that case, the existing exception and fallback behavior remains responsible for surfacing the provider error.

## Verification

- Unit tests verify provider-specific output limits.
- Paper-detail chat tests verify the high paper budget is passed into the primary and recovery streams.
- Existing streamed empty-response tests continue to validate retry behavior.
