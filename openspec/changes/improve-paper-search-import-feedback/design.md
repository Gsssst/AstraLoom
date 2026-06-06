## Context

The paper library already mixes local papers, saved papers, collection papers, reading-list papers, and remote previews from arXiv, Semantic Scholar, OpenAlex, Google Scholar, or a combined scholarly source. Remote previews expose `remote_id`, `remote_ingest_token`, `pdf_url`, and `source_url`, while frontend state tracks newly ingested remote keys.

Open-source paper discovery tools commonly emphasize source transparency and save/import readiness because users need to decide whether a search hit is actionable before adding it to a library. This project has the necessary fields already, so the improvement can stay in the frontend.

## Goals / Non-Goals

**Goals:**
- Show a compact count summary for current search-result states.
- Let users filter current results by local/importable/imported/open-PDF/missing-ID states.
- Make result cards use one consistent status tag set.
- Reset status filters sensibly when a new source/search result set is loaded.

**Non-Goals:**
- Add duplicate detection against existing local papers beyond current in-session ingest state.
- Change remote provider search behavior, ranking, or pagination.
- Add a backend endpoint for global import status lookup.
- Change collection, reading-list, or maintenance center APIs.

## Decisions

- Compute result state in the frontend from existing fields and in-session `ingestedRemoteIds`.
  - Rationale: no API migration is required and the UI can immediately reflect a successful import.
  - Alternative considered: backend returns canonical import status for each remote result; deferred because it needs provider-specific identifier matching and would be a larger data contract change.
- Add a local result-status filter independent from provider source.
  - Rationale: provider source chooses where to search, while status filter answers what action can be taken on the returned set.
  - Alternative considered: more source options; rejected because the source selector is already dense.
- Preserve empty-state recovery actions.
  - Rationale: filtering to a narrow status can legitimately show zero results; users need a clear reset path.

## Risks / Trade-offs

- [Risk] A remote result imported before the current session may still appear as importable.
  -> Mitigation: label the filter as current-result/action readiness and keep the post-import state accurate after this session's import.
- [Risk] Extra controls can crowd the search bar.
  -> Mitigation: place status counts and filters in a compact row below provider guidance instead of the primary search line.
- [Risk] Filtering can hide results unexpectedly after source changes.
  -> Mitigation: reset the status filter to `all` when search source changes.
