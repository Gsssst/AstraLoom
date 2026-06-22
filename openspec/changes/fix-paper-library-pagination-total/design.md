## Context

`GET /api/papers/search` already returns `items`, `total`, `page`, and `page_size`. The paper-library frontend currently requests `page_size: 30`, stores only `items`, and renders the page subtitle from `papers.length`, so a 42-paper library appears as 30 papers with no navigation to the second page.

Collection, saved, and reading-list views use separate list endpoints and do not currently expose the same pagination contract, so this fix focuses on `/papers/search` backed views: local library, "mine", and remote scholarly sources.

## Goals / Non-Goals

**Goals:**
- Store and display the `/papers/search` total for paginated search-backed views.
- Let users navigate search-backed result pages.
- Reset to page 1 when source, sort, filters, or URL-driven search context changes.
- Keep selected papers, ingestion, and result-state filtering behavior intact within the current loaded page.

**Non-Goals:**
- Add backend pagination to collection, saved, or reading-list endpoints.
- Change search ranking, query semantics, or page size limits.
- Add infinite scroll or virtualized rendering.

## Decisions

- Use Ant Design `Pagination` below the result list for search-backed views.
  - Rationale: it exposes total, page size, and page transitions explicitly and matches the existing UI library.
  - Alternative considered: "加载更多"; rejected because users need deterministic page navigation and the backend already has page-based pagination.
- Keep a single page state for both local and remote search-backed views.
  - Rationale: the backend already accepts `page` for both local and remote search. This removes the existing special case where only remote sources can advance.
  - Alternative considered: preserve `remotePage` and add `localPage`; rejected because it duplicates behavior with no product benefit.
- Show loaded item count as secondary context when the current status filter hides some loaded records.
  - Rationale: the top subtitle should answer total matching papers, while the result-state filter only applies to the loaded page.

## Risks / Trade-offs

- [Risk] Result-state status counts remain scoped to the current loaded page, not all matching pages.
  -> Mitigation: keep labels tied to visible/current results and use the page total only for the top-level library count.
- [Risk] Existing selected IDs can include papers from previous pages.
  -> Mitigation: preserve the current selected-ID behavior and keep export/update warnings for selected papers that are not in the current list.
