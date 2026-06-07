## 1. Backend Gap Feedback APIs

- [x] 1.1 Add request models and owner-scoped endpoints for saving one gap's feedback and refining one gap.
- [x] 1.2 Implement service helpers to normalize editable gap fields, rating, labels, notes, and evidence ids.
- [x] 1.3 Implement single-gap refinement with LLM JSON output and deterministic fallback.

## 2. Generation Feedback Binding

- [x] 2.1 Summarize Gap Map feedback into generation context from the current run.
- [x] 2.2 Include edited gap feedback in candidate generation and tree-evolution prompts.
- [x] 2.3 Persist gap feedback summary in run review metadata after proposal generation.

## 3. Frontend Gap Review UX

- [x] 3.1 Add editable per-gap controls for text fields, rating, labels, notes, and save action.
- [x] 3.2 Add linked evidence display inside each gap card using the current Evidence Map.
- [x] 3.3 Add single-gap refine action with focus note and refresh the returned run state.

## 4. Verification

- [x] 4.1 Add backend tests for gap feedback persistence, refinement fallback, and feedback-aware generation context.
- [x] 4.2 Add frontend contract tests for gap feedback controls, evidence display, and refine endpoint usage.
- [x] 4.3 Run targeted backend tests, frontend contract tests, frontend build, and OpenSpec validation.
