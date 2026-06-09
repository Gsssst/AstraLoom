## Context

The first six-pack implementation deliberately kept logic close to the UI for speed. The code now contains duplicated or shallow heuristics, especially citation key generation and metadata readiness. The user wants fewer new features and more algorithmic depth, so this change consolidates those judgments and makes them verifiable.

## Goals / Non-Goals

**Goals:**
- Centralize research workbench algorithms in a pure frontend service.
- Preserve existing UI surfaces while improving the values displayed.
- Add deterministic tests for citation keys, metadata quality, duplicate detection, evidence confidence, and graph edge strength.

**Non-Goals:**
- Add a new page or workflow.
- Integrate GROBID or a graph database.
- Change backend models or API contracts.

## Decisions

- Use a shared `researchAlgorithms.ts` service.
  - Rationale: pure functions are easier to test and keep UI components thinner.
- Use weighted quality scoring instead of a simple ready-count percent.
  - Rationale: DOI/arXiv and full text matter more than tags for downstream retrieval and writing.
- Treat DOI/arXiv matches as strong duplicates and normalized title matches as probable duplicates.
  - Rationale: identifier collision is more reliable than fuzzy title comparison.
- Score evidence confidence with current-paper evidence, coverage, insufficient flags, and reference source diversity.
  - Rationale: a single web reference should not imply the same confidence as several current-paper evidence chunks.
- Keep graph rendering unchanged but improve edge strength inputs.
  - Rationale: algorithm improvements should not add more visual complexity.

## Risks / Trade-offs

- Frontend-only algorithms can diverge from backend retrieval scoring -> use labels like readiness/confidence, not absolute truth.
- Heuristics may still be imperfect -> tests focus on stability and relative behavior, not universal correctness.
