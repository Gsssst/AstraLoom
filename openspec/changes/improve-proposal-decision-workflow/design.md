## Context

The Research Idea Workbench already persists enriched proposal data: decision status, review score, novelty/feasibility scores, evidence references, validation metadata, and evolution lineage. The current Top Proposal tab renders those proposals as an accordion in received order, so users must manually inspect each item to determine which one to advance.

External automated research systems commonly separate generation from review/ranking: generated ideas are scored, filtered, then promoted for follow-up work. This project already has the review signals needed for that pattern, so the first improvement should be a frontend decision surface rather than a backend scoring redesign.

## Goals / Non-Goals

**Goals:**
- Make the strongest proposal visible immediately after generation.
- Let users sort proposals by existing review and score signals.
- Let users filter by decision status without losing comparison and detail actions.
- Expose concise counts and recommendation cues near the proposal list.

**Non-Goals:**
- Change the workbench scoring algorithm or selected top proposal persistence.
- Add a new backend ranking endpoint.
- Add bulk decision actions.
- Replace the existing detailed proposal panels.

## Decisions

- Compute proposal ranking in the frontend from existing idea fields.
  - Rationale: all needed signals are already present in `Idea`, so the change remains low-risk and does not alter persisted data.
  - Alternative considered: add backend-computed rank metadata; deferred until ranking needs to be shared across pages or users.
- Default sort by aggregate review score, then novelty/feasibility fallback.
  - Rationale: aggregate review best reflects the multidimensional rubric, while older proposals without aggregate data still sort sensibly.
  - Alternative considered: recency default; rejected because users most often need quality triage after generation.
- Keep rejected proposals visible through a status filter.
  - Rationale: rejected ideas are useful history but should not dominate the default decision workflow.
- Highlight one recommended proposal among non-rejected items.
  - Rationale: a single visual anchor reduces scan cost without removing user control.

## Risks / Trade-offs

- [Risk] Frontend ranking can diverge from future backend ranking logic.
  -> Mitigation: keep ranking helper names explicit and contract-test the controls rather than treating the score as a new canonical backend field.
- [Risk] Filtering can hide selected comparison items.
  -> Mitigation: keep comparison count visible and allow returning to all proposals.
- [Risk] Score fields can be missing on older proposals.
  -> Mitigation: use zero/default fallbacks and keep recency sort available.
