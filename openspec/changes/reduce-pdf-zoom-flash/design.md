## Context

The PDF reader currently binds the active zoom state directly to `Page width={renderedPageWidth}`. This means every zoom step changes the React-PDF page width. During fast wheel/pinch gestures, React-PDF replaces or repaints large canvas layers repeatedly, which appears as white flashing.

The previous CSS-transform implementation avoided flashing but produced blurry pages because the final result was a scaled low-resolution canvas. This change keeps the good part of both approaches: CSS transform for short-lived visual feedback only, followed by high-resolution rendering after input settles.

## Goals / Non-Goals

**Goals:**
- Avoid visible white flashing during continuous PDF zoom gestures.
- Preserve sharp final rendering after the user stops zooming.
- Preserve scroll anchor behavior, text selection, page tracking, evidence highlighting, and native fallback behavior.
- Keep implementation scoped to the current React-PDF viewer.

**Non-Goals:**
- Replacing React-PDF or implementing full PDF.js virtualization.
- Adding a global rendering cache for all pages.
- Changing backend PDF extraction or evidence retrieval.

## Decisions

- Split zoom state into display and render zoom.
  - `displayZoomScale` drives toolbar percentage, scroll sizing, and transient visual scale.
  - `renderZoomScale` drives React-PDF `Page width`.
  - Rationale: Layout can respond immediately without forcing React-PDF to recreate canvases for every wheel event.

- Debounce render zoom updates.
  - Rationale: Wheel/pinch gestures emit many small events. A short idle delay batches them into one high-resolution render.
  - Use a delay around 180ms to balance responsiveness and reduced flashing.

- Apply CSS transform only to bridge display/render difference.
  - Rationale: While the final canvas is catching up, scaling the existing canvas avoids blank gaps. Once `renderZoomScale` catches up, transform returns to scale 1 and the rendered page is crisp.

## Risks / Trade-offs

- During an active zoom gesture, the preview may be slightly less sharp until the debounce settles. This is acceptable because it lasts only during interaction and prevents flashing.
- Evidence highlighting during the transient preview uses the existing text layer and may be visually scaled. Once the render settles, text and highlight coordinates align again.
- Large zoom jumps still require a high-resolution re-render after settling, which may take time on slow machines, but it should no longer re-render for every gesture tick.
