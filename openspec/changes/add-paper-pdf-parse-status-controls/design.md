## Context

The parser pipeline now supports lightweight, command, and Docling backends, and stores structured extraction under `metadata_json["pdf_structured_content"]`. Stable use requires users to see whether that metadata exists and administrators to rerun parsing after enabling a better backend or after a parsing failure.

Related product patterns from RAG/document systems:
- RAGFlow exposes document parsing as an inspectable ingestion step with parser choices and chunk-level grounding.
- Document management systems such as paperless-ngx treat processing state and retry paths as operational first-class features.

## Goals / Non-Goals

**Goals:**
- Show structured PDF parse status on paper detail.
- Include parse status in the existing processing status API.
- Allow admins to force structured parsing from an existing PDF path or by first loading the arXiv PDF.
- Persist parser source, counts, parsed timestamp, and failures in metadata.
- Keep paper Q&A usable when parse status is missing or failed.

**Non-Goals:**
- Add a background job queue UI.
- Add block-level inspection UI.
- Add a database migration or new parser result table.
- Let non-admin users trigger expensive parsing.

## Decisions

1. Derive status from existing metadata.
   - Rationale: `Paper.metadata_json` already stores structured parse output and avoids migration risk.
   - Alternative considered: new `paper_parse_jobs` table. Rejected until asynchronous job history is needed.

2. Add `POST /papers/{paper_id}/reparse-structured-pdf`.
   - Rationale: this is specific to structured metadata and does not conflate with full-text loading.
   - Behavior: ensure a PDF path exists, optionally load full text/PDF first for arXiv papers, run `extract_pdf_structured_content`, persist metadata, return status.

3. Surface status in both detail and maintenance APIs.
   - Rationale: users need per-paper transparency while admins need queue-like repair actions.

## Risks / Trade-offs

- [Risk] Synchronous reparse can be slow. -> Admin-only endpoint and frontend loading state; existing parser timeouts still apply.
- [Risk] Metadata can be stale when parser backend changes. -> Status includes parser source and reparse action.
- [Risk] Parse failure hides evidence. -> Store failure metadata and keep lightweight/full-text fallback.
