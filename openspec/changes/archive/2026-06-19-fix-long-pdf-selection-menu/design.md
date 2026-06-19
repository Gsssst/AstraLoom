## Context

The PDF viewer reports selected text through `onTextSelect`, and the paper detail page renders a fixed-position contextual menu. The current PDF handler only reports selections shorter than 800 characters and relies on `Range.getBoundingClientRect()`. For longer multi-line selections, this causes two problems: selections above the limit are ignored entirely, and large range rectangles can produce unstable menu placement.

## Goals / Non-Goals

**Goals:**

- Show the contextual selection menu for long multi-line PDF selections.
- Keep the menu within the viewport and near the visible selected text.
- Preserve existing actions and page-number capture.

**Non-Goals:**

- No backend changes.
- No changes to saved annotation schema.
- No redesign of the toolbar controls.

## Decisions

1. **Raise the PDF selection character cap instead of removing bounds entirely.**

   A bounded cap protects the chat, annotation, and notes flows from accidental full-document selections. A higher cap still supports full paragraphs and page-sized excerpts.

2. **Derive the menu anchor from visible client rects.**

   `Range.getClientRects()` exposes per-line rectangles. Selecting the first visible non-empty rectangle gives a stable anchor near the beginning of the selection, even when the overall range spans many lines. Fall back to `getBoundingClientRect()` only if no usable client rect exists.

3. **Keep page detection from the selection anchor.**

   The existing page capture can continue to use the selection anchor node and current page fallback. This fix is about eligibility and menu placement, not page-region precision.

## Risks / Trade-offs

- [Risk] A very long accidental selection may still produce a large quote or annotation. -> Keep a cap and trim whitespace before sending.
- [Risk] Anchoring to the first visible line may not be exactly where the mouse ended. -> It is more stable than using the full multi-line bounding rectangle and keeps the menu visible.
