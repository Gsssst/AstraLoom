## Context

The paper detail page uses `react-pdf` to render PDF pages with text and annotation layers. The current implementation keeps `Page width={pageWidth}` fixed and applies `transform: scale(zoomScale)` to a wrapper. That makes zooming fast, but it also enlarges the already-rendered canvas and causes visible blur at high zoom.

Mature PDF viewers re-render pages at the active scale. React-PDF exposes `Page` `width` and `scale` props for this purpose, and PDF.js stores current page scale as viewer state rather than treating zoom as a post-render CSS-only effect.

## Goals / Non-Goals

**Goals:**
- Keep formulas and small text sharp after zoom by rendering pages at the effective zoomed size.
- Preserve text selection, evidence highlighting, page tracking, and direct page jumps.
- Make touchpad/Ctrl-wheel zoom and toolbar zoom feel more responsive.
- Let users make the paper AI panel substantially wider for long answers.

**Non-Goals:**
- Replacing `react-pdf` with the full PDF.js viewer.
- Changing the browser-native fallback iframe zoom behavior.
- Adding virtualized page rendering in this change.

## Decisions

- Compute `renderedPageWidth = pageWidth * zoomScale` and pass that width directly to `Page`.
  - Rationale: React-PDF will render canvas, text layer, and annotation layer in the same coordinate system at the target display size.
  - Alternative considered: Keep CSS transform and raise the base canvas width. That still blurs once zoom exceeds the chosen base size and wastes memory at normal zoom.

- Keep a fit-to-panel base width and apply zoom as an explicit multiplier.
  - Rationale: The existing fit-to-width reset and scroll-anchor math already depend on a stable base width.

- Keep resize measurement paused while dragging the split.
  - Rationale: Re-rendering PDF pages on every split pointer move still causes white flashing. Existing resize pause logic should remain and only measure once the drag settles.

- Lower the PDF panel minimum width from 42% to 30%.
  - Rationale: This allows the AI panel to grow to roughly 70% of the workspace while still leaving a usable PDF column and preserving the existing chat collapse threshold.

## Risks / Trade-offs

- Rendering pages at high zoom uses larger canvases and more memory. The existing 400% max zoom remains in place to bound this cost.
- Re-rendering on zoom may briefly show page loading work on slower machines. This is still preferable to permanently blurry reading at high zoom.
- Very wide chat panels reduce PDF readability, but the user can drag the split back or collapse the chat rail.
