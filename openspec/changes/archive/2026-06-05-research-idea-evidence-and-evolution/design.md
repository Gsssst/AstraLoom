## Context

The first workbench stage persists local-library Evidence Maps, Gap Maps, reviewed candidate pools, and top proposals. It intentionally deferred external scholarly search and hypothesis evolution. The codebase already exposes shared arXiv and Semantic Scholar adapters, so this phase extends the independent workbench service instead of adding a second search implementation.

This phase continues the workflow direction inferred from `NoviScl/AI-Researcher`, `open-coscientist`, `SakanaAI/AI-Scientist-v2`, and `cheerss/SciPIP`: expand evidence coverage, keep provenance visible, let users narrow the candidate set, and evolve a selected hypothesis from critique rather than overwriting it.

## Goals / Non-Goals

**Goals:**

- Add an explicit external-search switch for workbench runs.
- Enrich the Evidence Map with failure-tolerant arXiv and Semantic Scholar results.
- Persist user decisions without deleting rejected proposals.
- Compare two to four proposals through one normalized structure.
- Create a traceable child proposal from one parent proposal and user focus.

**Non-Goals:**

- Automatically ingest every external result into the local paper library.
- Implement continuous autonomous hypothesis evolution.
- Add Elo tournaments, collaborative voting, or experiment execution.
- Depend on external search availability for successful workbench completion.

## Decisions

### External evidence is optional and failure tolerant

Extend the run request with `external_search`. When enabled, search Semantic Scholar and arXiv concurrently after local retrieval, normalize results, deduplicate by title and scholarly identifier, and add them to the inspiration evidence group. External items use stable identifiers such as `ext:semantic_scholar:<doi-or-arxiv-or-title-key>` and retain their source URL.

Alternative considered: automatically ingest external papers. Deferred because the workbench only needs provenance-aware evidence excerpts; ingestion adds network and storage side effects that should remain an explicit user action.

### Proposal decisions reuse status

Use the existing `ResearchIdea.status` field for `draft`, `pinned`, `rejected`, and existing downstream statuses such as `implemented`. Decision updates receive an allow-listed state and remain project-owner scoped.

Alternative considered: add a separate boolean for each decision. Rejected because the user-facing states are mutually exclusive and the existing status field already expresses lifecycle state.

### Evolution creates a child proposal

Add `parent_idea_id` and `evolution_json` to `ResearchIdea`. Evolution sends the parent hypothesis, review, evidence, experiment plan, and optional user focus to the LLM, normalizes the structured result, and persists a new draft proposal. The parent remains unchanged.

Alternative considered: overwrite the parent. Rejected because comparison, reproducibility, and later experiment reflection require inspectable lineage.

### Comparison stays deterministic

The comparison API returns normalized proposal data, review dimensions, evidence counts, experiment plans, statuses, and lineage. The browser renders the comparison table. It does not require a new LLM call.

Alternative considered: ask the model to choose a winner. Deferred because the first useful comparison feature should show trade-offs without implying an objective winner.

## Risks / Trade-offs

- [Risk] External APIs can be slow, rate-limited, or unavailable → Run sources concurrently, catch failures per source, store source errors, and complete with local evidence.
- [Risk] Duplicate external papers may appear under different identifiers → Normalize titles and prefer DOI, then arXiv ID, then a title key.
- [Risk] Proposal status can conflict with downstream states → Allow decision updates only for `draft`, `pinned`, and `rejected`; preserve `implemented`.
- [Risk] Evolution can drift away from evidence → Include parent evidence and review uncertainty in the prompt and persist the requested focus and rationale.

## Migration Plan

1. Add nullable parent and evolution metadata columns to `research_ideas`.
2. Extend the workbench run request and evidence normalizer.
3. Add authenticated proposal decision, comparison, and evolution endpoints.
4. Update the project page with external-search control and proposal actions.
5. Apply migration `020`, restart the backend, and run targeted tests and frontend build.

## Open Questions

- Should the next phase expose an explicit “ingest external paper” action from the Evidence Map?
- Should multi-round evolution stop based on score improvement, user review, or a configured iteration budget?
