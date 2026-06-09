## Context

The research idea workbench already builds an Evidence Map and Gap Map, generates candidate proposals, runs novelty checks, applies quality adjustments, and persists selected proposals. Recent work added facet-level novelty matrices and toolbox-fit plans. The next quality bottleneck is evidence grounding: a proposal can cite papers by ID while still making claims that are not clearly supported.

Related project patterns reviewed before implementation:

- AI-Researcher: combines related paper search, grounded idea generation, and proposal ranking/filtering.
- AI-Scientist: separates idea generation from novelty/review checks and relies on scholarly search metadata for evidence.
- Sisyphus Academica: uses citation verification and review gates before accepting generated academic text.
- eTracer/PaperTrail-style claim grounding: maps generated claims to supporting sources instead of treating citations as a flat list.

## Goals

- Make proposal evidence quality more explainable before users invest time in discussion, validation, or writing.
- Improve ranking by penalizing candidates whose evidence references are sparse, homogeneous, or weakly matched to claims.
- Persist enough metadata for UI inspection and downstream writing/validation reuse.

## Non-Goals

- Do not add a new standalone evidence-review page.
- Do not call external scholarly APIs during ranking.
- Do not introduce embeddings or new vector infrastructure.
- Do not require schema changes; metadata should fit existing JSON fields.

## Approach

### Evidence Grounding Matrix

For each candidate, derive a compact list of proposal claims from:

- hypothesis
- approach
- minimum experiment
- contribution-style phrasing in the title/description

For each claim, match relevant evidence items from the existing Evidence Map using normalized token overlap and candidate-provided `evidence_ids`. Each matrix row records:

- claim text
- claim type (`hypothesis`, `mechanism`, `experiment`, `contribution`)
- support level (`strong`, `partial`, `weak`, `missing`)
- supporting evidence refs with paper ID, title, category, source, and score
- risk note explaining the weakest part of the support

### Evidence Quality Scoring

The existing `evidence_coverage` signal will be extended with an `evidence_grounding_matrix` and a concise quality profile:

- claim coverage ratio
- strong support ratio
- source diversity
- category diversity
- explicit evidence ID usage
- missing or weak claims
- overall `grounding_score`

The score should be deterministic and cheap to compute.

### Ranking Adjustment

`apply_quality_adjustments` will reduce candidate scores when:

- any central hypothesis/contribution claim has missing support
- fewer than two evidence categories or sources support all claims
- candidate evidence IDs do not resolve to known evidence items

The penalty must be recorded in `quality_adjustments` and reflected in review metadata.

### Persistence and UI

When top proposals are persisted, store the evidence grounding metadata inside `review_json` and/or the proposal evidence payload. The research project page will display a compact evidence-grounding card in the existing proposal detail view with:

- grounding score
- claim support counts
- weak/missing claims
- supporting paper tags

## Risks

- Lexical matching may underrate semantically relevant evidence. Mitigation: keep the score advisory and combine explicit `evidence_ids` with text overlap.
- UI could become noisy. Mitigation: show only a compact summary and expand claim rows only when metadata exists.
