## Context

The paper detail page renders the PDF reader and AI Q&A as desktop split panes inside the shared app layout. The split handle updates React width state on every pointer move, and the desktop navigation sidebar expands/collapses with a width transition. `PDFViewer` observes its container with `ResizeObserver` and passes the changing width into each `react-pdf` `Page`, which causes pdf.js canvas pages to be re-rendered repeatedly during these intermediate layout widths. During those re-renders the page canvas can briefly clear to white.

## Goals / Non-Goals

**Goals:**

- Keep the visible PDF content stable during active split-pane dragging.
- Keep the visible PDF content stable during outer layout transitions such as desktop sidebar expand/collapse.
- Commit the final PDF panel width after the pointer interaction ends.
- Recalculate the PDF page width once after the resize settles so layout still matches the new panel size.
- Preserve current PDF controls, page jump, evidence locator, text selection, and gesture zoom behavior.

**Non-Goals:**

- Replacing `react-pdf` or pdf.js.
- Redesigning the paper detail layout.
- Changing backend paper chat or evidence retrieval behavior.

## Decisions

- Add an explicit "resize active" signal from `PaperDetailPage` to `PDFViewer`.
  - Rationale: The parent page knows when the split handle is being dragged. Passing that state lets the PDF viewer pause expensive width recalculation only during that interaction.
  - Alternative considered: debounce every `ResizeObserver` update. Debouncing still leaves repeated delayed redraws during long drags and makes ordinary container changes feel laggy.

- Freeze `PDFViewer`'s `pageWidth` while the PDF split handle is active, then measure once when the drag ends.
  - Rationale: The existing canvas remains mounted and visible while the panel width changes, avoiding blank redraw flashes. A single post-drag measurement keeps the final layout accurate.
  - Alternative considered: remount the whole PDF viewer after drag. That would lose scroll position and selection context.

- Debounce ordinary `ResizeObserver` page width measurements until the container width settles.
  - Rationale: AppLayout sidebar expansion is not a paper-detail pointer drag, so the viewer needs a local defense against any continuous container resize. Delaying the expensive `Page width` update keeps the current canvas visible during the transition and applies the final width once.
  - Alternative considered: wire AppLayout collapsed state into paper detail. That couples the PDF reader to global navigation internals and would not cover other layout-driven resizes.

- Keep width state updates in `PaperDetailPage` so panels still visually resize during drag.
  - Rationale: Users need immediate feedback from the split panes. Only the PDF canvas page size needs to be frozen, not the overall panel layout.

## Risks / Trade-offs

- [Risk] The PDF page may appear slightly narrower or wider than the panel while dragging. → Mitigation: the mismatch lasts only during the drag and the final width is applied immediately on pointer up.
- [Risk] The PDF page may lag behind the final panel width briefly after sidebar expansion. → Mitigation: apply the final measurement after a short settle delay so there is only one post-transition redraw.
- [Risk] Resize end events can be missed if the pointer leaves the window. → Mitigation: existing pointerup listener remains on `window`; cleanup also clears the active resize state.
- [Risk] Mobile panel switching should not be affected. → Mitigation: only activate the freeze state from the desktop split-handle drag path.
