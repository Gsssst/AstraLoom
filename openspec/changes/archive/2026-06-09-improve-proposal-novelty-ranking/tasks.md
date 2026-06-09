## 1. Backend Novelty Matrix

- [x] 1.1 Add facet extraction helpers for research question, mechanism, experiment, contribution, and evidence overlap.
- [x] 1.2 Build `novelty_matrix` inside candidate novelty checks with nearest collision and differentiation notes.
- [x] 1.3 Add novelty matrix summaries to run review summary and persisted proposal metadata.

## 2. Ranking and Repair

- [x] 2.1 Strengthen quality adjustment and selection ranking penalties using matrix collision risk and missing differences.
- [x] 2.2 Add deterministic anti-collision repair candidates for high-risk candidates.
- [x] 2.3 Ensure repaired candidates retain provenance and remain subject to deduplication/review.

## 3. Frontend Display

- [x] 3.1 Add compact proposal detail rendering for novelty facets, nearest collision, real differences, and missing differences.
- [x] 3.2 Keep existing novelty collision UI intact when matrix metadata is absent.

## 4. Verification

- [x] 4.1 Add backend tests for novelty matrix, ranking penalty, and anti-collision repair.
- [x] 4.2 Add frontend contract tests for novelty matrix display.
- [x] 4.3 Run backend tests, frontend tests/build, and OpenSpec validation.
- [x] 4.4 Commit implementation and archive the OpenSpec change.
