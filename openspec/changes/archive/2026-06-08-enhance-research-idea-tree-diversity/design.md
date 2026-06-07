## Context

The Workbench currently creates candidate hypotheses, expands them with three deterministic operators, deduplicates by token overlap, reviews candidates, checks novelty collisions, runs adversarial review, and persists the top-scoring proposals.

That pipeline is inspectable and stable, but the search tree can produce shallow variants. Similar projects suggest a stronger pattern:
- Open Coscientist-style systems use a generate, review, rank, evolve, and deduplicate loop.
- AI-Researcher-style idea pipelines separate generation, deduplication, ranking, and filtering.
- Multi-agent ideation experiments show that diverse critics and interaction depth improve idea variety, but uncontrolled expansion can create noise.

This change adopts a bounded version of those patterns.

## Goals / Non-Goals

**Goals:**
- Add LLM-assisted critique-and-evolve expansion for top frontier candidates.
- Preserve rule-based fallback expansion for invalid or failed model output.
- Select final proposals with diversity-aware reranking instead of pure aggregate score.
- Persist selection rationale, diversity facets, and suppressed candidate metadata.
- Keep existing staged progress, review, novelty, and adversarial signals compatible.

**Non-Goals:**
- Full multi-agent orchestration framework.
- Long-running autonomous literature review.
- New database tables or migrations.
- Replacing the current review rubric.

## Decisions

### Use a bounded LLM evolution call per generation run

The service will call the model once with the current frontier, evidence summary, and Gap Map. The model returns evolved candidates using operators such as:
- mechanism_shift
- stronger_baseline
- failure_mode
- cost_aware
- cross_domain_transfer

The response is normalized through the existing candidate normalizer. If the call fails or returns too few valid candidates, deterministic fallback mutation fills the gap.

### Keep deterministic tree metadata

Every root and evolved candidate keeps `tree.round`, `tree.operator`, `tree.parent_title`, and `tree.lineage`. LLM-evolved candidates also store concise `critique`, `improvement`, and `selection_angle` fields so the UI can explain how a proposal changed.

### Diversity-aware selection happens after final adjusted scores

After review, novelty adjustment, and adversarial penalty, the service will select top proposals using a simple MMR-style score:

`selection_score = adjusted_score - diversity_penalty + facet_bonus`

The diversity penalty is based on overlap with already selected proposal facets and title/hypothesis tokens. Facets are deterministic labels derived from path, tree operator, experiment dataset, evidence ids, and risk/metric tokens.

### Persist selection rationale without migration

Selected Ideas already persist `review_json`. The new selection metadata is added there:
- `selection_rationale`
- `selection_score`
- `diversity_facets`
- `suppressed_duplicates`

The run `review_summary` also records the diversity selection summary.

## Risks / Trade-offs

- Extra model call may slow generation → one bounded batch call only; fallback keeps generation working.
- LLM-evolved candidates may be malformed → reuse JSON parser, normalizer, and deterministic fallback.
- Diversity selection may choose a slightly lower-scoring idea → persist the selection score and rationale so the tradeoff is visible.
- Facet labels are heuristic → treat them as explainable selection hints, not ground truth.
