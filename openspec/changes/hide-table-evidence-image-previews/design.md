## Context

Visual evidence references are shown in two places on the paper detail chat: compact citation chips and optional preview cards. The preview card is useful for figures and architecture diagrams, but table crops are often not legible at thumbnail size and can show broken/awkward image boxes.

Evidence-heavy answers can also include many current-paper references. Showing every preview and chip immediately after each answer makes the chat hard to scan. Similar RAG chat products typically present citations as an expandable source/evidence region so the answer remains readable while evidence remains available on demand.

The paper library maintenance center currently exposes structured parsing and visual evidence extraction as adjacent top-level batch actions. The structured parser still supports backend readiness and repair flows, but the current user-facing path for multimodal PDF evidence is visual evidence extraction.

## Goals / Non-Goals

**Goals:**

- Hide image preview cards for table-like evidence.
- Collapse reference details by default in paper Q&A answers.
- Preserve table citation chips, page navigation, evidence counts, and tooltips.
- Preserve image previews for non-table visual evidence.
- Keep the current visual evidence batch action prominent in the maintenance center.
- Remove the old structured PDF parse batch button from the top maintenance action row.

**Non-Goals:**

- Do not remove table evidence from Q&A context or backend references.
- Do not change visual evidence extraction, OCR, or asset routes.
- Do not remove backend structured PDF parse endpoints or single-paper repair affordances that are still needed for diagnostics.

## Decisions

- Add a frontend predicate for table-like evidence types/kinds and exclude those references from `visualPreviewReferences`.
- Keep reference color and chip logic unchanged so table evidence remains visible as `[E]` tags.
- Add local per-message expanded/collapsed state for paper chat evidence references.
- Render a compact evidence summary by default with confidence, coverage, total evidence count, and visual evidence count where available.
- Render preview cards and citation chips only when the user expands the references.
- Remove only the prominent `backfill-structured-pdf?limit=5` top-level batch button; keep the visual evidence batch button and backend routes intact.

## Risks / Trade-offs

- [Risk] Some high-quality table images might be useful. -> Users can still jump to the PDF page from the chip; a dedicated full-size table viewer can be added later if needed.
- [Risk] Hiding citation chips by default might make evidence feel less discoverable. -> The compact summary shows counts and a clear "查看引用" action.
- [Risk] Removing the structured parse batch button could hide a useful admin action. -> Structured parsing remains available through backend flows and targeted repair where needed; the top row should avoid confusing it with the current visual evidence method.
