## 1. Backend Tree Evolution

- [x] 1.1 Add LLM-assisted critique-and-evolve candidate expansion with JSON normalization.
- [x] 1.2 Preserve deterministic fallback operators and tree metadata when evolution is unavailable.

## 2. Backend Diversity Selection

- [x] 2.1 Add deterministic diversity facets and MMR-style top proposal selection.
- [x] 2.2 Persist selection rationale, selection score, diversity facets, and suppressed duplicate metadata.

## 3. Frontend Selection Signals

- [x] 3.1 Extend Proposal detail rendering to show selection rationale and diversity facets.
- [x] 3.2 Keep selection signals compact alongside existing novelty, adversarial, and search-tree signals.

## 4. Verification

- [x] 4.1 Add backend tests for LLM evolution, fallback expansion, and diversity-aware selection.
- [x] 4.2 Add frontend contract tests for selection rationale UI markers.
- [x] 4.3 Run targeted backend tests, frontend contract tests, frontend build, and OpenSpec validation.
