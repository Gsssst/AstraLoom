## Context

The maintenance panel now exposes health and repair actions. The next improvement is interpretability: diagnostics should explain why a branch missed, and the UI should suggest what to repair first. Chat and paper Q&A already emit status events, so low-coverage transparency can be added without changing the streaming protocol shape.

## Goals / Non-Goals

**Goals:**
- Explain diagnostic misses in human-readable Chinese.
- Recommend bounded repair actions based on current index coverage and missing artifacts.
- Make low retrieval coverage visible during answer generation.
- Keep recommendations cheap: aggregate counts plus small samples.

**Non-Goals:**
- Building an automatic background scheduler.
- Re-ranking diagnostics with a new model.
- Guaranteeing that every missed query has a single exact cause.

## Decisions

### Diagnostics return explanations next to branch results

The diagnostics endpoint adds `query_terms`, `summary`, `branch_explanations`, and `recommended_actions`. Explanations are heuristic but grounded in observable state: BM25 readiness, embedding coverage, branch errors, branch result counts, and match-source flags.

### Recommendations are action-oriented

The recommendations endpoint returns grouped cards for full-text backfill, embedding backfill, and BM25 rebuild. Each card has severity, reason, suggested endpoint/action, and sample papers.

### Low-coverage status stays in existing stream events

The existing `status` stream event is extended with coverage-aware text. This keeps frontend stream parsing stable while making answer quality limitations visible.

## Risks / Trade-offs

- [Heuristic explanations may be imperfect] -> Phrase them as likely causes and include observed signals.
- [Embedding coverage requires a count query] -> This is cheap compared with answer generation and already used elsewhere.
- [Long recommendation lists could clutter UI] -> Return bounded samples and short reasons.

## Migration Plan

1. Add backend explanation/recommendation models and helper functions.
2. Extend diagnostics and add recommendations endpoint.
3. Extend retrieval status wording for low/no source coverage.
4. Update settings maintenance UI.
5. Add tests and run validation.
