## Context

The paper detail page currently has two selection paths. PDF selections call `onTextSelect(text, pageNumber)` and immediately create a quote card. Non-PDF selections show a small fixed popup for asking or explaining. Existing React PDF ecosystems such as `react-pdf-viewer` model highlight interactions around a selection target/content renderer, and `react-pdf-highlighter`-style workflows center on a tooltip near the selected region. This change uses the same interaction pattern without replacing the current PDF renderer or adding a dependency.

## Goals / Non-Goals

**Goals:**
- Use one contextual menu model for PDF and paper-detail text selections.
- Keep the user in control of whether selected text becomes a quote, prompt, note, annotation, or copied text.
- Reuse existing backend endpoints and state: paper chat, annotations, and personal notes.
- Keep the menu compact, keyboard/screen-reader labeled, and mobile-aware.

**Non-Goals:**
- Persist visual PDF highlights on the document canvas.
- Add a new annotation backend model or full highlight coordinate storage.
- Replace `react-pdf` with another PDF viewer.

## Decisions

- Use one `selectionMenu` state with `{ text, pageNumber?, x, y, source }`.
  - Rationale: avoids duplicated popup paths and allows PDF selections to show actions without immediately mutating the composer.
  - Alternative considered: keep PDF auto-insert and only improve the popup UI. That preserves the current surprise behavior and does not solve accidental selections.
- Extend `PDFViewer` `onTextSelect` to include viewport coordinates.
  - Rationale: the parent owns the menu and action semantics; the viewer only reports text and where the selection ended.
  - Alternative considered: render the menu inside `PDFViewer`. That would duplicate chat, notes, and annotation state in the viewer component.
- Keep annotation saving available only for PDF selections with a page number.
  - Rationale: the current annotation model stores page-based PDF quotes. Non-PDF article text can still be added to notes, copied, or used in chat.
- Append note snippets locally and then let users save through the existing note save button.
  - Rationale: this avoids hidden writes and gives users a chance to edit the note.

## Risks / Trade-offs

- Selection coordinates can be near viewport edges -> clamp the floating menu with responsive CSS and calculated bounds.
- Users may expect saved annotations from non-PDF text -> show save annotation only when a PDF page is known; use notes for other text.
- Browser selection may remain visible after an action -> clear `window.getSelection()` after action execution.
