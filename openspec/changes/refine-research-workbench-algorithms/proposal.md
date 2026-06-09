## Why

The six research workbench enhancements added useful surfaces, but several core judgments are still page-local heuristics. To avoid making the product heavier, the next step should improve the underlying algorithms and centralize them as testable pure functions rather than adding more UI.

## What Changes

- Move citation-key, metadata-quality, duplicate-risk, evidence-confidence, and graph-edge scoring into a shared algorithm module.
- Improve citation keys using normalized author/year/title tokens and stable suffixes.
- Improve duplicate detection with normalized title and DOI/arXiv identifiers rather than exact title only.
- Improve metadata quality scoring with weighted checks for identifiers, full text, embeddings, tags, and citation readiness.
- Improve evidence confidence with source-aware reference scoring.
- Improve graph edge strength selection using evidence/category/score metadata where available.

## Capabilities

### New Capabilities

### Modified Capabilities
- `research-workbench-six-pack`: existing research workflow panels SHALL use shared, testable algorithms for quality, confidence, and relationship scoring.

## Impact

- Frontend algorithm service and focused tests.
- Existing paper detail, paper library, writing, and research project pages.
- No new user-facing modules and no backend schema changes.
