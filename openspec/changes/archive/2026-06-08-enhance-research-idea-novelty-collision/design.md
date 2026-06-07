## Context

The Research Idea Workbench already generates inspectable proposals through evidence retrieval, Gap Map extraction, candidate generation, search-tree expansion, deduplication, LLM review, token-overlap novelty checks, adversarial review, and top-proposal persistence.

The weak point is novelty/collision detection. It currently compares candidate text against the evidence map using lexical overlap only. Similar prior work can be missed when it appears outside the initial evidence set or uses different wording.

Similar open-source systems suggest a pragmatic pattern:
- AI-Scientist-style novelty checks iterate scholarly queries and make an explicit novelty decision from retrieved papers.
- AutoResearchClaw-style research agents rely on multiple scholarly sources and degrade gracefully when a source fails.
- AutoSci-style novelty endpoints combine web/scholarly/local evidence with an LLM-facing review object.

This project should adopt the lightweight version of that pattern without adding a new dependency or migration.

## Goals / Non-Goals

**Goals:**
- Enrich each candidate's `novelty_check` with ranked `similar_work` entries.
- Use both local evidence and external scholarly search when the run is configured for external search.
- Produce a clear collision risk level, nearest evidence, source coverage, and rationale for downstream validation/UI.
- Keep generation resilient when arXiv/Semantic Scholar search fails.
- Preserve existing API shapes by extending JSON metadata rather than adding a table.

**Non-Goals:**
- Full autonomous literature review or citation graph analysis.
- New paid search provider integration.
- Blocking Idea generation on external source availability.
- Replacing the current LLM review rubric or search-tree expansion in this change.

## Decisions

### Similar-work pool is built once per reviewed batch

The service will build a candidate-aware similar-work pool before novelty checks. It will contain:
- all current evidence map items;
- optional external scholarly results for a compact query derived from high-scoring candidate titles/hypotheses and the project brief.

This avoids running one network search per candidate, which would slow generation and amplify rate-limit risk.

### Deterministic scoring first, LLM-free

Collision ranking will combine:
- token overlap between candidate title/hypothesis/approach and paper title/abstract;
- title overlap as a stronger collision signal;
- source/category weight so seed/background evidence is trusted more than generic inspiration;
- recency/source metadata where available.

This keeps tests deterministic and makes the generation path independent of another model call.

### Store enriched results in existing metadata

Selected Ideas already persist `review_json.novelty_check`. The new fields will be added there:
- `collision_risk`: `high|medium|low|unknown`
- `similar_work`: ranked list with paper id, title, source, year, score, relation, and reason
- `source_coverage`: counts and source errors

No schema migration is required because `review_json` is JSON.

### UI shows concise collision evidence

The Proposal detail view will continue showing the existing novelty status, but it will add the top similar-work entries and source coverage. The validation API can reuse the same `similar_work` list for related work.

## Risks / Trade-offs

- External source latency → perform a single batch query and keep graceful fallback to local evidence.
- Lexical matching is imperfect → expose evidence and risk as review aid, not as an absolute truth.
- Query drift from candidate aggregation → constrain the query with project brief and top candidate terms only.
- UI clutter → show only the top few similar works and use compact metadata rather than a large literature panel.
