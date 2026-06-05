## Context

The research-direction page currently exposes project creation, recommended papers, and one-shot idea generation. The resulting ideas are difficult to trust because the intermediate evidence, research gaps, candidate alternatives, and review reasoning are not visible. The replacement must integrate with the existing paper library and ownership rules without depending on the legacy idea-generation algorithm.

The design borrows product and workflow principles from several open-source research-agent projects:

- `NoviScl/AI-Researcher`: iterative literature collection, grounded candidate generation, semantic deduplication, ranking, and novelty/feasibility filtering.
- `open-coscientist`: literature reflection, multidimensional review, ranking, proximity analysis, and hypothesis evolution.
- `SakanaAI/AI-Scientist-v2`: structured idea objects, reflection rounds, novelty checking, and experiment-oriented proposals.
- `cheerss/SciPIP`: separating background papers from inspiration papers and generating ideas through multiple paths.

## Goals / Non-Goals

**Goals:**

- Make the Idea formation process inspectable and evidence-grounded.
- Store intermediate artifacts so users can revisit a run after refresh.
- Generate proposals that include falsifiable hypotheses and minimum viable experiment plans.
- Stream stage progress to the browser and keep the existing project ownership boundary intact.
- Introduce the new pipeline independently from the legacy one-shot algorithm.

**Non-Goals:**

- Automatically execute generated experiment code.
- Build a full scientific knowledge graph in the first iteration.
- Implement Elo tournaments or multi-round hypothesis evolution in the MVP.
- Replace the existing paper ingestion, paper detail, chat, or writing-assistant flows.

## Decisions

### Persist each workbench run

Add `ResearchIdeaRun` as a project-owned record containing run configuration, current stage, progress, evidence map, Gap Map, candidate pool, review summary, and error details. Intermediate artifacts use JSON columns for the MVP because they are consumed as complete workbench views and do not yet need cross-project analytics.

Alternative considered: keep artifacts only in browser state. Rejected because refreshes, long-running model calls, and later iteration would lose provenance and make debugging difficult.

### Keep enriched proposals compatible with existing ideas

Extend `ResearchIdea` with a nullable run reference and structured JSON fields for evidence, review details, and experiment plan. Keep the existing title, description, approach, novelty, scores, discussion log, and generated code fields so existing discussion and code-generation endpoints remain usable.

Alternative considered: create a second proposal table. Rejected because it would split selected ideas from existing discussion and code flows without adding value in the MVP.

### Use an independent staged service

Create `ResearchIdeaWorkbenchService` rather than adding more branches to the legacy pipeline. Its stages are:

1. `briefing`
2. `retrieving`
3. `mapping_gaps`
4. `generating`
5. `deduplicating`
6. `reviewing`
7. `selecting`
8. `complete`

The service emits stage snapshots through a callback and persists each stage so synchronous and streamed API paths share one implementation.

Alternative considered: wrap the legacy service. Rejected because the requested behavior is structurally different and must not inherit opaque prompt assumptions.

### Start with local-library evidence and an explicit evidence taxonomy

The MVP combines papers explicitly attached to a project with local-library matches and classifies them as `seed`, `background`, or `inspiration`. Every stored evidence item includes paper identity, title, abstract excerpt, source category, and why it matters. External scholarly search can be added as a later adapter without changing the workbench contract.

Alternative considered: add web search immediately. Deferred because provenance and a useful local workflow matter more than increasing source count in the first slice.

### Generate and review structured candidates

Candidates use a structured schema: title, path, gap, hypothesis, approach, evidence IDs, risks, falsification test, and minimum experiment. Review uses six explainable dimensions: novelty, evidence grounding, feasibility, testability, impact, and clarity. The aggregate score is weighted but each dimension and rationale remains visible.

### Stream progress with Server-Sent Events

Expose an SSE endpoint that emits `stage`, `artifact`, `idea`, `done`, and `error` events. Persisted run details remain available from a normal JSON endpoint for refresh recovery.

Alternative considered: WebSocket. Deferred because each run is a one-way progress stream and SSE is simpler to operate within the existing API.

## Risks / Trade-offs

- [Risk] Model JSON may be malformed or omit fields → Validate and normalize every stage, persist an actionable run error, and provide deterministic fallback structures where useful.
- [Risk] Local-library-only evidence can miss recent work → Show source scope clearly and keep the service adapter boundary ready for external scholarly search in a follow-up change.
- [Risk] JSON artifacts become difficult to query as usage grows → Normalize evidence and review records later if cross-project analytics or collaborative editing requires it.
- [Risk] Long-running runs can monopolize an HTTP worker → Use streamed progress in the MVP and keep the execution boundary compatible with a background queue in a later iteration.
- [Risk] Users may mistake scores for objective truth → Show score rationale, supporting papers, conflicts, and uncertainty rather than a single opaque number.

## Migration Plan

1. Add nullable structured fields to `research_ideas` and create `research_idea_runs`.
2. Deploy the independent workbench service and new API endpoints without removing legacy endpoints.
3. Switch the research project detail page to the new run flow while preserving existing projects and ideas.
4. Verify refresh recovery, ownership boundaries, proposal persistence, and frontend production build.
5. Keep rollback straightforward by leaving legacy idea fields and endpoints intact.

## Open Questions

- Which external scholarly-search provider should be the first follow-up adapter: Semantic Scholar, OpenAlex, or a configurable hybrid?
- Should later hypothesis evolution use pairwise Elo comparison, user-driven comparison only, or both?
