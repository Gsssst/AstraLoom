## 1. LLM Output Limit Policy

- [x] 1.1 Add provider-aware output token ceilings to the LLM service.
- [x] 1.2 Clamp retry escalation against the active provider ceiling.

## 2. Paper Q&A Integration

- [x] 2.1 Pass the provider-aware paper Q&A budget into streamed paper-answer generation.
- [x] 2.2 Pass the same budget into recovery and non-streamed paper Q&A generation.

## 3. Verification

- [x] 3.1 Add or update backend tests for provider-specific paper Q&A limits.
- [x] 3.2 Run targeted tests and OpenSpec validation.
- [ ] 3.3 Commit the implementation and archive the completed OpenSpec change.
