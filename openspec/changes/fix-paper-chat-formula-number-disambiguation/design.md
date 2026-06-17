## Context

The current paper chat path sends the user question, history, attachments, and retrieval toggles. Unless the user explicitly selects PDF text, backend retrieval does not know which PDF page the user is reading. For numbered formulas, this creates an ambiguity: `(2)` can appear in different sections/pages, and the first extracted match may be unrelated to the visible formula.

## Goals / Non-Goals

**Goals:**
- Carry a bounded `reading_context.current_page` from the PDF viewer to paper chat.
- Use the current page as a strong preference for formula-number evidence.
- Keep fallback behavior for cases where no current-page formula is found.
- Make evidence metadata disclose when page-context disambiguation was used.

**Non-Goals:**
- Do not implement a full formula search engine or MathML index in this change.
- Do not OCR screenshots or infer formulas from rendered PDF pixels.
- Do not change answer rendering or KaTeX behavior.

## Design

### Frontend

- Extend `PDFViewer` with an optional `onPageChange(page: number)` callback.
- Fire the callback when scroll/jump/target-page changes update the current page.
- Store the current PDF page in `PaperDetailPage`.
- Include `{ reading_context: { current_page } }` in `/ask-stream` and `/ask` payloads when available.
- If the user selects PDF text, preserve the explicit quote in the question and include its page as the current page.

### Backend

- Extend `AskPaperRequest` with optional `reading_context`.
- Pass `reading_context.current_page` into `build_paper_context_with_evidence`.
- Extend `retrieve_evidence_with_plan` / `retrieve_evidence` with `preferred_pages`.
- For `formula_number` strategy:
  - try `_numbered_formula_text_evidence` on preferred pages first;
  - then try all page text;
  - then fallback to full text and structured formula order.
- Add metadata such as `preferred_page_match` and `preferred_pages` to matched formula evidence.

## Risks / Trade-offs

- Current page is heuristic when the PDF scroll position is between pages. Mitigation: prefer a small page window `{page-1,page,page+1}` if needed, but start with exact page preference.
- If the user asks a global formula question while viewing a different page, page preference could bias retrieval. Mitigation: only apply it to explicit numbered formula questions and still fall back globally if no page-local match exists.
