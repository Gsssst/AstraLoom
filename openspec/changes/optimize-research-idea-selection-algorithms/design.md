## Context

The idea workbench already generates a multi-path candidate pool, expands it through a bounded search tree, performs novelty and adversarial checks, and selects diverse proposals. However, the selection layer can still keep weaker duplicates, underweight evidence provenance, and choose superficially different proposals that share the same gap or experiment shape. The user wants algorithm depth rather than more product surface.

## Goals / Non-Goals

**Goals:**

- Improve deterministic candidate deduplication and selection quality.
- Keep existing API contracts and persisted JSON shapes compatible.
- Make scoring decisions inspectable through metadata that can already be displayed by existing proposal panels.
- Add tests that exercise algorithm behavior directly.

**Non-Goals:**

- Add new UI panels or workflow entry points.
- Change database schema or migrations.
- Introduce a graph database, embedding model, or new external search provider.
- Replace LLM candidate generation; this change improves deterministic post-processing.

## Decisions

- Use composite candidate similarity.
  - Rationale: title/hypothesis overlap alone misses paraphrases and over-merges candidates that share broad vocabulary. Combining title, hypothesis, gap, approach, experiment facets, and evidence overlap better reflects proposal redundancy.
- Merge duplicates by pre-review quality.
  - Rationale: tree expansion can produce a stronger child after a weaker parent. Keeping the first item makes quality depend on generation order rather than candidate content.
- Add evidence coverage profiles before final quality adjustment.
  - Rationale: a candidate grounded in multiple seed/background papers and sources should score differently from one with a single weak inspiration item.
- Fold scoring signals into existing `review_json`.
  - Rationale: no schema change is needed because selected ideas already persist review metadata as JSON.
- Keep thresholds deterministic and conservative.
  - Rationale: these scores rank candidates within a run; they should be stable, explainable, and easy to test.

## Risks / Trade-offs

- Composite similarity can still miss semantic duplicates without embeddings -> mitigate by preserving LLM novelty checks and using multiple lexical/facet signals.
- Evidence coverage can over-reward broad but shallow evidence -> mitigate by capping evidence bonuses and requiring experiment completeness.
- Stronger duplicate replacement can change selected proposal order -> mitigate with deterministic tie-breakers and tests.
- Metadata growth can make JSON larger -> mitigate by storing concise profiles and summaries only.
