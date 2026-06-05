# Design

## Collection Diagnostics

`GET /api/folders/{folder_id}/diagnostics` returns:

- `paper_count`
- `full_text_count` / `full_text_coverage`
- `embedding_count` / `embedding_coverage`
- `read_status_counts`
- `ready_for_idea`
- `warnings`

The folder list also embeds a compact diagnostic summary so collection selectors can show coverage at a glance.

## Research Seed Provenance

The research project creation request accepts `collection_ids`. The backend resolves the user's owned collections and stores:

```json
{
  "seed_collections": [
    {"id": "...", "name": "...", "paper_ids": ["..."]}
  ]
}
```

During idea workbench evidence collection, seed papers are annotated with `collection_ids` and `collection_names`. Persisted ideas include a `collection_sources` summary in `referenced_papers` and `evidence_json`.

## Direct External Ingest To Collection

The frontend reuses the existing `/papers/ingest-personal` endpoint, then calls `/folders/{folder_id}/papers` with the returned local paper ID when a target collection is selected. This keeps the ingestion API focused and avoids adding hidden folder coupling to scholarly providers.

## UX

Paper library:

- Collection selector shows coverage and readiness tags.
- Remote result cards get an "加入分类" action when a target collection is selected.

Research page/detail:

- Creation modal displays selected collection coverage hints.
- Evidence maps and idea cards show collection-origin tags for generated ideas.
