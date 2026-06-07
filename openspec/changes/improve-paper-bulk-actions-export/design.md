## Context

The paper library already tracks selected local paper IDs in `selectedIds`. It can add multiple papers to a collection through `POST /folders/{id}/papers`, update one paper's read status through `PUT /papers/{id}/read-status`, generate group reports from selected paper IDs, and export BibTeX through an existing writing endpoint. The current selected-paper bar is functional but visually dense, partly prompt-driven, and offers only one generic export.

Reference scan before coding:
- Zotero and JabRef center selected item operations around explicit selected-entry export and collection/library actions.
- Paperless-ngx exposes a clear selection mode with batch edit actions after documents are selected.

The practical pattern for this project is a persistent selected-paper toolbar that groups safe bulk operations, uses explicit format choices, and reports partial failures instead of hiding multi-step results behind a single toast.

## Goals / Non-Goals

**Goals:**
- Make selected-paper actions easier to scan and use.
- Export selected local papers as BibTeX, Markdown, and JSON without adding backend work.
- Bulk update reading status using the existing endpoint.
- Reuse existing collection and report flows.
- Keep mobile/narrow layouts usable.

**Non-Goals:**
- Add server-side batch export endpoints.
- Add bulk delete or global destructive operations.
- Add new import providers or change paper search.
- Change permission rules for admin-only batch tagging.

## Decisions

- Build exports from selected papers currently loaded in the page.
  - Rationale: this supports the common case immediately and avoids adding backend surface area.
  - Alternative considered: add a `/papers/export-selected` endpoint; deferred until users need exporting items that are not in the current result set.

- Run reading-status bulk updates as bounded per-paper requests.
  - Rationale: reuses the existing authorization and saved-state behavior in `/papers/{id}/read-status`.
  - Alternative considered: add a new bulk read-status endpoint; deferred to keep this change frontend-only.

- Present one fixed toolbar with grouped sections.
  - Rationale: selected-item bars in literature/document tools work best when count, destination, export, status, and clear actions are visible at once.
  - Alternative considered: hide all actions in a dropdown; rejected because bulk export and collection actions are frequent.

- Treat partial failures as first-class feedback.
  - Rationale: multi-request actions can partially succeed. The user needs counts and recovery guidance rather than an all-or-nothing message.

## Risks / Trade-offs

- [Risk] Client-side export only includes selected papers that are in the current page data.
  -> Mitigation: the UI selection is also page-local today, so this matches the current selection model.

- [Risk] Bulk reading updates can trigger several requests.
  -> Mitigation: selected page batches are small and the UI summarizes success/failure counts.

- [Risk] More toolbar controls can crowd narrow screens.
  -> Mitigation: use responsive wrapping and stable class hooks.
