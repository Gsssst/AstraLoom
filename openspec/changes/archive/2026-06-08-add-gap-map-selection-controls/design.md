## Context

The Workbench currently executes evidence retrieval, Gap Map extraction, candidate generation, search-tree expansion, review, novelty collision checking, adversarial review, and diverse selection in one continuous run. That is efficient, but users cannot steer the most important step: which research gaps should become proposals.

Similar systems point toward staged human-in-the-loop control:
- Open Coscientist-style workflows expose staged hypothesis generation, ranking, and evolution rather than hiding all intermediate artifacts.
- Open AI Co-Scientist-style systems treat generated hypotheses as artifacts that can be refined and prioritized.
- Research canvas tools such as open-research-ANA emphasize user-guided collection and continuation instead of one-shot automation.

This design keeps the current one-click path but adds a preview-and-continue path for users who want control.

## Goals / Non-Goals

**Goals:**
- Let users run evidence + Gap Map extraction without immediately generating proposals.
- Let users choose selected gaps, blocked gaps, a focus note, research mode, risk appetite, and resource budget.
- Bind candidate generation, tree evolution, and selection rationale to the selected gaps and constraints.
- Persist the selected constraints in existing run JSON fields and selected Idea review metadata.
- Preserve existing one-click generation and streaming behavior with default constraints.

**Non-Goals:**
- Multi-user collaborative gap voting.
- New database tables or migrations.
- Full rewrite of the run lifecycle into a background queue.
- Blocking existing API consumers that call `/generate-ideas` or `/idea-runs/stream`.

## Decisions

### Add a preview endpoint rather than changing default generation

The new endpoint creates a persisted run, executes through evidence retrieval and Gap Map extraction, stores artifacts, sets the run to `gap_review`, and returns the run. Existing generation endpoints continue to run end-to-end.

### Continue generation from a reviewed run

A second endpoint accepts selected gap titles/ids and constraints, updates the run config, filters/annotates the Gap Map, and continues from candidate generation through selection. This avoids recomputing evidence and keeps the staged artifacts recoverable after refresh.

### Use JSON metadata only

Selected gaps and constraints are stored in:
- `ResearchIdeaRun.config_json.gap_selection`
- `ResearchIdeaRun.config_json.generation_constraints`
- `ResearchIdeaRun.review_summary.gap_selection`
- selected `ResearchIdea.review_json.gap_selection`

No migration is needed.

### Candidate prompts receive selected Gap Map and constraints

`generate_candidates` and `evolve_candidate_frontier` will receive a constrained Gap Map. The prompt will explicitly include research mode, risk appetite, resource budget, selected gaps, blocked gaps, and focus note. Fallback candidates will also use the filtered gaps.

## Risks / Trade-offs

- Users may select no gap → default to all gaps and record that fallback.
- Users may overconstrain generation → include constraints as guidance, but keep fallback candidates available.
- API misuse could continue a run owned by another user → reuse existing owner-scoped run/project checks.
- More UI controls could clutter the Workbench → use compact cards, segmented controls/selects, and keep the existing one-click button.
