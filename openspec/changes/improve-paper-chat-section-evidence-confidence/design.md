## Context

The retrieval layer already detects explicit numbered-section requests and stores `target_section_number` and `matched_section_heading` in each evidence reference's `metadata.evidence_plan`. The API metadata reducer currently drops that semantic distinction and computes coverage as `len(evidence) / 3`, which makes one exact section range look weak.

The frontend confidence helper also assumes higher evidence counts always mean stronger grounding. That is reasonable for broad questions, but incorrect for exact section requests where one extracted section range is the intended evidence unit.

## Goals / Non-Goals

**Goals:**
- Surface targeted section hits from backend evidence metadata.
- Treat exact numbered-section hits as sufficient even with one reference.
- Make the UI label and drawer copy clear that this is a targeted section match.

**Non-Goals:**
- Do not increase retrieval breadth for section questions.
- Do not alter LLM prompts or answer generation.
- Do not change evidence scoring for non-section questions.

## Decisions

- Derive `target_section_number`, `matched_section_heading`, and `section_evidence_match` in `_paper_evidence_meta()`.
  - Rationale: The API already sees all references for both normal and streaming endpoints, so this keeps behavior consistent.
  - Alternative considered: Recompute confidence only in the frontend from references. That would duplicate backend semantics and would not persist cleanly in saved chat history.

- Set `evidence_coverage` to `1.0` and `evidence_insufficient` to `false` for exact section matches.
  - Rationale: In this retrieval strategy, one range is the expected complete answer basis.
  - Alternative considered: Show a separate badge while keeping coverage at 33%. That preserves a misleading number.

- Extend frontend confidence status with `section`.
  - Rationale: Users should see why a single evidence reference can still be strong.

## Risks / Trade-offs

- False section confidence if the matched heading is wrong -> The backend only sets the flag when both target and matched heading exist in the evidence plan.
- Single truncated section could still be incomplete -> The existing reference snippet and drawer remain available; this change only fixes the confidence label, not the underlying extraction budget.
