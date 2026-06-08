## 1. Backend Claim Safety

- [x] 1.1 Add deterministic section claim extraction helpers to the writing project service.
- [x] 1.2 Extend section citation checks to return `claim_diagnostics` and `claim_safety_summary` while preserving existing `checks`.
- [x] 1.3 Add backend tests for uncited claims, weak supported claims, and external-only evidence.

## 2. Frontend Diagnostics

- [x] 2.1 Update `SectionEditor` to render claim safety summary after citation checks.
- [x] 2.2 Show risky claim rows with status labels, sentence text, citation markers, and next actions.
- [x] 2.3 Update frontend contract tests for the new diagnostic UI.

## 3. Verification

- [x] 3.1 Run focused backend writing tests.
- [x] 3.2 Run focused frontend contract tests, frontend build, and OpenSpec validation.
