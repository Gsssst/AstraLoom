## Context

Remote previews already carry identifiers such as arXiv ID, DOI, provider remote ID, title, PDF URL, and source URL. Local paper ingestion also performs duplicate checks, but that feedback happens too late: the user only learns after clicking an import action. Search and digest/push cards need the same duplicate awareness before the action is shown.

## Goals / Non-Goals

**Goals:**

- Mark remote previews as already in the local library when they match an existing `Paper`.
- Reuse the same matching rules across remote search and digest/push preview lists.
- Disable import actions and show "已在论文库" for matched previews.
- Preserve existing personal save/import behavior for genuinely new papers.

**Non-Goals:**

- Merge duplicate local paper records.
- Change ingestion idempotency or duplicate resolution semantics.
- Add a separate manual duplicate-management screen.
- Block opening PDFs/source links for already-in-library papers.

## Decisions

1. Add a backend preview-annotation helper.
   - Rationale: Matching by identifiers and normalized title should be consistent no matter which provider produced the preview.
   - Alternative considered: frontend-only matching against currently loaded local results. Rejected because search/digest surfaces can show papers outside the current page and matching must include DOI/arXiv/provider metadata.

2. Use layered matching: arXiv ID, DOI, remote/source metadata, then normalized title fallback.
   - Rationale: Stable identifiers should win, but some providers omit DOI/arXiv IDs. Title fallback catches common digest/search cases while keeping exact normalized title matching conservative.

3. Return explicit fields instead of overloading `remote_id`.
   - Rationale: `local_paper_id` and `in_library` are clear to UI clients and do not change the meaning of provider identifiers.

4. Keep import endpoints idempotent.
   - Rationale: The UI should prevent redundant clicks, but backend idempotency remains necessary for stale clients and race conditions.

## Risks / Trade-offs

- [Risk] Title-only matching can produce false positives for very generic titles. -> Mitigation: use exact normalized title as a fallback only after identifier checks.
- [Risk] Large remote result sets could cause many local queries. -> Mitigation: annotate a bounded preview list and batch local lookups by identifiers/titles.
- [Risk] Existing digest payloads may not contain every identifier. -> Mitigation: annotate with whatever fields are available and leave action enabled when no confident match exists.
