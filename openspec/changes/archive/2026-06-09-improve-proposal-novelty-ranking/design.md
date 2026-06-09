## Context

The Research Idea Workbench already collects similar work and stores an aggregate novelty result. The current check uses title/candidate text overlap and source bonuses, which is useful for coarse ranking but not enough to tell whether a proposal is genuinely different from the nearest paper.

Open-source research-agent systems such as AI-Researcher and AI-Scientist treat novelty checking as a dedicated review stage over related papers. This change keeps the local architecture lightweight by adding deterministic facet analysis over the existing similar-work pool instead of adding another model call or external service.

## Goals / Non-Goals

**Goals:**

- Build a `novelty_matrix` for each candidate against top similar works.
- Compare facets: research question, mechanism, experiment setup, contribution claim, and evidence overlap.
- Generate concise differentiation notes and missing-difference risks.
- Use the facet matrix to penalize ranking and selection when a candidate is too close to prior work.
- Try a deterministic repair candidate when a candidate is too similar.
- Display the matrix summary in existing Proposal details.

**Non-Goals:**

- No new external search provider.
- No database migration.
- No second LLM review pass for every candidate.
- No full citation graph or semantic embedding rewrite.

## Decisions

### Facet matrix over existing similar-work pool

`_novelty_check` will call a helper like `_novelty_matrix(candidate, ranked_similar_work)` after top similar papers are scored. The helper returns:

- `facet_scores`: question, mechanism, experiment, contribution, evidence overlap.
- `differentiation`: concise real differences and missing differences.
- `nearest_collision`: top related work with facet-level reasons.
- `collision_risk`: high, medium, low, or unknown.

This keeps compatibility with existing `novelty_check` metadata while adding richer detail.

### Deterministic repair pass

For candidates with `collision_risk=high`, create at most one revised candidate using deterministic text adjustments:

- Preserve the original evidence and minimum experiment.
- Add an `anti_collision_revision` field recording the nearest work and avoided facets.
- Shift approach text toward missing differences, stronger baselines, and a narrower falsification test.

This is intentionally conservative. The repair pass produces another candidate for review/selection, not an automatic replacement.

### Ranking penalties

Quality adjustment will use matrix risk:

- `high`: strong novelty penalty unless repaired.
- `medium`: moderate penalty.
- `low`: no extra penalty.

Selection rationale will include the novelty risk and nearest collision when present.

### UI display

The existing Proposal detail novelty panel will show the novelty matrix compactly:

- facet risk tags
- nearest collision
- differentiation notes
- missing differences

No new page is added.

## Risks / Trade-offs

- [Risk] Lexical facet matching can miss semantic overlap. → Keep similar work and matrix details visible for manual review and keep the aggregate novelty result conservative.
- [Risk] Deterministic repair may produce awkward text. → Treat repaired candidates as additional candidates subject to normal review, not as guaranteed improvements.
- [Risk] Strong penalties may hide useful incremental ideas. → Use collision risk rather than raw similarity alone, and preserve medium-risk candidates when their experiment or evidence differs meaningfully.
