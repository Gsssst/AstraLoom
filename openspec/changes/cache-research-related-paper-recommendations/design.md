## Context

The research detail page now loads related-paper recommendations without blocking the core workbench, but the backend recommendation endpoint still recomputes on every visit. `PaperSelectionService.select_papers` can call LLM entity extraction, LLM query generation, semantic retrieval, arXiv search, Semantic Scholar search, and LLM reranking. Repeating that work for unchanged project inputs wastes time and API budget.

## Goals / Non-Goals

**Goals:**
- Reuse related-paper recommendations when the research project inputs have not changed.
- Give users an explicit refresh action when they want new recommendations.
- Keep cache storage lightweight and migration-free by using existing project metadata.
- Keep the existing recommendation algorithm intact.

**Non-Goals:**
- Redesign `PaperSelectionService`.
- Add a background job or queue for recommendations.
- Add a new database table.
- Cache generated Idea workbench runs.

## Decisions

- Store cached recommendations under `ResearchProject.metadata_json["related_paper_recommendations"]`.
  - Rationale: the cache is project-scoped, small, and derived from existing project fields.
  - Alternative considered: a new table; rejected because this change does not need queryable history.
- Include a deterministic cache key derived from project name, description, keywords, and manual paper IDs.
  - Rationale: recommendations become stale when those inputs change.
- Add a `refresh` query parameter to the existing endpoint.
  - Rationale: it preserves the endpoint URL while giving the frontend a manual recompute path.
- Return cache metadata alongside the papers.
  - Rationale: the frontend can show when data is cached and whether refresh is running.

## Risks / Trade-offs

- [Risk] Cached recommendations may miss newly ingested papers until refreshed.
  → Mitigation: provide an explicit refresh button in the related-papers card.
- [Risk] Metadata JSON mutation may not be detected by SQLAlchemy if mutated in place.
  → Mitigation: assign a new metadata dictionary to `project.metadata_json` before committing.
- [Risk] Older frontend code may expect a bare array response.
  → Mitigation: the updated frontend reads the new object shape; this is an internal app endpoint used by the current frontend.
