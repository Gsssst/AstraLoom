## Context

The paper API already accepts `page`, `year_from`, and `year_to`, but remote discovery does not forward an offset into scholarly provider adapters. The frontend also does not expose publication-year fields and presents only a two-line abstract preview. As a result, repeated remote searches return the same upstream batch and users cannot inspect enough metadata before deciding whether to ingest a paper.

## Goals / Non-Goals

**Goals:**

- Forward an explicit remote offset into arXiv, Semantic Scholar, and OpenAlex discovery.
- Add a clear “换一批” interaction that advances the remote batch while preserving query and year filters.
- Reset remote pagination when search conditions change.
- Add publication-year range controls for local and remote discovery.
- Let users inspect the full available abstract without ingesting the paper first.

**Non-Goals:**

- Randomize scholarly ranking.
- Persist search history.
- Fetch a full PDF when a user opens the abstract modal.

## Decisions

### Use deterministic page offsets instead of randomization

The API will translate page numbers into provider offsets. arXiv and Semantic Scholar receive an offset directly. OpenAlex receives a one-based page computed from the offset. Deterministic paging avoids repeated results while keeping searches reproducible.

### Keep abstract inspection local to the current preview

The detail modal will use the abstract already returned by the search endpoint. This keeps the interaction immediate and avoids another external request.

### Validate year ranges in the interface

The interface will reject a start year greater than the end year before sending a request. The backend continues to enforce field bounds.

## Risks / Trade-offs

- [Risk] A fallback provider can rank papers differently between pages. → Preserve the requested offset across providers and keep each batch deterministic for the active upstream response.
- [Risk] Some records have no abstract. → Show a clear “暂无摘要” state in the modal.
- [Risk] Filters add density to the search bar. → Place year controls and the remote refresh action on a compact secondary row.

