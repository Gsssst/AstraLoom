## Context

P1/P2 has already added evidence cards, citation checks, citation decision metadata, and writing workbench summaries. The next gap is draft quality: users need local feedback on whether a section is ready to polish/export or still needs evidence, comparison, or a clearer gap.

## Goals / Non-Goals

**Goals:**
- Provide section-level quality scoring without extra LLM cost.
- Return structured dimensions: claim, evidence, comparison, gap, structure.
- Give actionable rewrite guidance for each weak dimension.
- Integrate the check into the existing `SectionEditor`.

**Non-Goals:**
- Generate a complete rewritten section.
- Persist quality reports in the database.
- Replace citation verification.
- Add paragraph-by-paragraph LLM grading.

## Decisions

- Use deterministic heuristics.
  - Rationale: quality feedback should be instant, reproducible, and cheap.
  - Alternative considered: LLM review. That can be deeper, but would introduce token cost and variability.
- Analyze section text plus title only.
  - Rationale: this keeps the endpoint simple and makes it usable before citations are fully configured.
- Keep citation check separate but complementary.
  - Rationale: citation checks answer "does this citation support the sentence"; quality checks answer "is this section structurally ready."

## Risks / Trade-offs

- [Risk] Heuristics may miss nuanced writing quality. → Mitigation: labels are framed as diagnostic hints, not final review.
- [Risk] Users may expect automatic rewriting. → Mitigation: return rewrite hints and actions rather than pretending to produce final text.
- [Risk] More buttons could clutter the editor. → Mitigation: add one compact `质量评估` action next to citation check.
