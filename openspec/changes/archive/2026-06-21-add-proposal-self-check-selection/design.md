## Context

The previous change made proposals easier to read and added a manual "深入打磨" action. The next weakness is timing: users still receive Top Proposals that may not have been tightened before being shown. This change adds an automatic self-check after selection and before persistence.

External patterns:

- AI-Scientist-style systems connect ideas to experiment templates; the self-check should force the minimum experiment and failure condition to be concrete.
- STORM-style systems outline before expansion; the self-check should rewrite the compact brief rather than expanding more panels.
- Self-Refine/Reflexion-style loops use critique to improve the next answer; this product should apply a single bounded critique-and-rewrite pass only to selected proposals to control cost and latency.

## Goals

- Tighten Top Proposal briefs before they are saved.
- Make the self-check transparent through stored metadata.
- Avoid rerunning full generation or changing the number of proposals.
- Keep fallback deterministic if the LLM response is unavailable.

## Non-Goals

- Do not add a new autonomous agent loop.
- Do not re-rank all candidates after self-check in this change.
- Do not change user-facing generation controls.
- Do not create child proposal versions.

## Backend Design

Pipeline insertion:

1. Generate, expand, deduplicate, review, novelty-check, adversarial-review, adjust quality, and select as today.
2. Run `self_check_selected_proposals(selected, brief, evidence_map, gap_map, generation_context)`.
3. Persist the self-checked selected proposals.

Self-check input:

- candidate title, gap, hypothesis, approach, current `idea_brief`, `proposal_outline`, review, novelty check, evidence grounding, experiment completeness, selected gap constraints, and evidence facets.

Self-check output:

- `selection_self_check`:
  - `status`: `tightened` or `fallback`
  - `critique`: novelty, scope, mechanism, experiment, failure-condition notes
  - `rewrite_summary`
  - `used_evidence_ids`
  - `quality_gates`
- updated `idea_brief`
- optionally tightened `falsification_test` and `minimum_experiment` fields when present

Fallback:

- Build critique from existing novelty/adversarial/experiment metadata.
- Preserve candidate fields.
- Normalize `idea_brief` again so it remains complete.

## Frontend Design

The proposal detail already defaults to Idea Brief and collapsed secondary information. Add a compact self-check indicator:

- In the Idea Brief card header, show a small tag when `review.selection_self_check` exists.
- Inside the existing collapsed "打磨审查" or secondary details, show self-check critique summary and quality gates.
- Do not add another large always-visible panel.

## Testing

- Backend:
  - self-check normalizes and attaches metadata
  - fallback self-check works with invalid model output
  - persistence stores `selection_self_check` and updated `idea_brief`
- Frontend contract:
  - type includes `selection_self_check`
  - UI references the self-check tag and folded critique
- Verification:
  - focused pytest
  - frontend contract test
  - OpenSpec strict validation
  - frontend build
