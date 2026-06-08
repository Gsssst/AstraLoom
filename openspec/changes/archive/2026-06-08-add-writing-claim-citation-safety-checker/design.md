## Context

The backend already exposes `POST /writing/projects/{project_id}/citations/check-section`, which maps bracket citation markers to writing-project evidence cards and returns per-citation support checks. The frontend `SectionEditor` displays those checks and next actions.

The missing layer is claim safety. A section can contain important claims with no citation marker at all, or a citation marker that points to external-only evidence. Similar projects such as RefChecker separate textual claims from cited evidence and then classify whether support is strong, partial, weak, missing, or unverifiable. This change implements a lightweight local version using existing sentence parsing, citation extraction, evidence cards, and paper match scoring.

## Goals / Non-Goals

**Goals:**
- Add deterministic claim-level diagnostics to section citation checks.
- Preserve the existing `checks` response shape so existing UI remains compatible.
- Make unsupported and unverified claims visible in the section editor.
- Keep the implementation fast and bounded to local project evidence.

**Non-Goals:**
- Do not add a new LLM fact-checking pipeline.
- Do not fetch web evidence or external PDFs during checking.
- Do not block editing, saving, or exporting automatically.
- Do not mutate draft text automatically.

## Decisions

1. **Extend the existing check-section endpoint.**
   - Rationale: claim safety is part of citation support, and the frontend already has a button and diagnostic area for this workflow.
   - Alternative: add a new endpoint. That would duplicate evidence lookup and split the UX.

2. **Use heuristic claim extraction first.**
   - Rationale: sentence-level scanning is fast, deterministic, testable, and adequate for highlighting likely unsupported claims.
   - Alternative: use LLM claim extraction. Better recall is possible, but cost and latency are not justified for the first version.

3. **Attach each claim to citation mentions inside the same sentence.**
   - Rationale: existing citation checks already score sentence/evidence support; reusing those statuses keeps results explainable.
   - Alternative: infer cross-sentence citation support. This is riskier and harder to explain.

4. **Return safety summary and next actions.**
   - Rationale: users need a prioritized result, not only a list of warnings.

## Risks / Trade-offs

- Heuristic claim extraction may miss subtle claims -> label output as safety diagnostics, not formal verification.
- Some valid claims may cite a previous sentence -> mark as missing citation unless same sentence has a marker; users can still decide.
- Existing evidence snippets may be sparse -> external or weak support remains visible instead of being overconfidently accepted.
