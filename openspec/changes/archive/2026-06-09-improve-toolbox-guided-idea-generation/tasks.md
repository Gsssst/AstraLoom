## 1. Backend Tool-Fit Planning

- [x] 1.1 Add deterministic tool-fit scoring helpers for selected toolbox entries and Gap Map items.
- [x] 1.2 Build and attach `tool_fit_plan` in generation context before candidate generation.
- [x] 1.3 Include `tool_fit_plan` in prompt constraints for candidate generation and candidate evolution.
- [x] 1.4 Update fallback candidate generation to use top-ranked tool-fit items.
- [x] 1.5 Persist tool-fit plan and rationale in review summary and selected proposal metadata.

## 2. Frontend Proposal Display

- [x] 2.1 Add proposal detail rendering for used tools and tool-fit rationale.
- [x] 2.2 Keep the display compact and hidden when no tool-fit metadata exists.

## 3. Verification

- [x] 3.1 Add backend tests for deterministic tool-fit planning and fallback usage.
- [x] 3.2 Add frontend contract tests for proposal tool-fit display.
- [x] 3.3 Run backend tests, frontend tests/build, and OpenSpec validation.
- [x] 3.4 Commit implementation and archive the OpenSpec change.
