## Context

The existing Research Scout mode uses the shared scholarly search service and returns deterministic candidate metadata to the chat UI. The next gap is not provider breadth; it is interpretation quality. Users may ask for papers from specific labs, companies, universities, venues, or authors, and they may want explicit evaluation along dimensions such as novelty and reproducibility.

Comparable open-source systems inform the direction:
- PaperQA2 combines scientific metadata, retrieval, LLM-based reranking, and cited answers.
- STORM and GPT Researcher expose research workflow state rather than hiding retrieval behind prose.
- OpenResearcher treats scientific search, filtering, and answer refinement as tool-like steps.

## Goals / Non-Goals

**Goals:**
- Parse venue, institution, author, hard/soft constraint, and evaluation-focus hints from the user query.
- Preserve deterministic card data even when the LLM answer is interrupted or unavailable.
- Evaluate candidate papers through a structured rubric with `score`, `reason`, `evidence`, and `confidence`.
- Make missing evidence explicit by lowering confidence and avoiding unsupported claims.
- Render the new intent and evaluation fields compactly in the chat workbench.

**Non-Goals:**
- Full affiliation enrichment from external author-profile APIs.
- New database columns for venue or affiliations.
- Bulk ingestion or automatic side effects.
- A full agent tool execution framework; that belongs to Phase 2.

## Decisions

1. **Use deterministic evaluation first.**
   - The backend scores candidates from available title, abstract, year, source, authors, citations, PDF status, and query terms.
   - Rationale: the UI contract remains stable and testable even without an LLM JSON call.

2. **Let the LLM explain from structured context.**
   - Candidate context sent to the model includes parsed constraints and rubric summaries.
   - Rationale: the model can give useful prose while the card-level metadata remains bounded by evidence.

3. **Treat institution matching as evidence-limited.**
   - If provider metadata does not expose affiliations, institution matching checks visible title, abstract, and author text only and reports `unknown` confidence when absent.
   - Rationale: most scholarly search APIs do not consistently return affiliations in lightweight search results.

4. **Represent constraints as hard or soft.**
   - Queries containing "必须", "只要", "only", "must", "限定", or "hard" mark constraints as hard; otherwise constraints are soft preference signals.
   - Rationale: this lets the UI and assistant distinguish filtering intent from ranking preference.

## Risks / Trade-offs

- **Affiliation metadata may be incomplete** -> show uncertain matches instead of filtering candidates away silently.
- **Heuristic scoring can be approximate** -> present scores as "评估" with evidence/confidence, not ground truth.
- **More card data can overwhelm the chat** -> keep score chips compact and put details in tooltip-like secondary text.
