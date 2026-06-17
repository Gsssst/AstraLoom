## Context

The paper detail view uses `react-pdf` to render pages into canvas and text layers inside an application scroll container. The rejected local magnifier cloned rendered page DOM into a floating loupe, which made small areas larger but did not match the interaction users expect from Chrome/PDF.js-style viewers.

Mature PDF viewers use page-level scale changes rather than a cloned local lens for this workflow. Mozilla PDF.js exposes zoom through viewer scale updates and handles pinch zoom with an origin point, while `react-pdf` exposes `Page` `width`/`scale` props that resize the canvas and text layer together. `react-pdf-viewer` also handles trackpad pinch as a non-passive wheel listener gated by `ctrlKey`.

## Goals / Non-Goals

**Goals:**
- Provide global PDF zoom in the enhanced reader through toolbar buttons and gesture wheel events.
- Keep page text, annotations, text selection, and evidence highlighting in the same rendered coordinate system.
- Preserve the user's viewport anchor when zooming so the page does not jump back to the top.
- Avoid browser-level page zoom when the user's gesture is intended for the PDF pane.

**Non-Goals:**
- Replacing the current `react-pdf` renderer.
- Implementing app-controlled zoom for the browser-native iframe fallback.
- Adding a minimap, crop viewer, or local loupe.

## Decisions

- Use a `zoomScale` multiplier on top of the current fit-to-panel `pageWidth`.
  - Rationale: Existing layout already computes a responsive base width. Multiplying it keeps fit-to-width behavior simple and lets the `Page` canvas/text/annotation layers stay aligned.
  - Alternative considered: CSS `transform: scale(...)`. That would enlarge pixels without rerendering the text layer and would break scroll sizing and selection accuracy.

- Handle pinch / Ctrl-or-Cmd wheel through a native `wheel` listener with `{ passive: false }`.
  - Rationale: Trackpad pinch in Chromium is delivered as a wheel event with `ctrlKey`, and preventing default must be reliable to avoid zooming the whole browser tab.
  - Alternative considered: React `onWheel`. It is simpler, but native listener options are closer to established PDF viewer implementations and more explicit.

- Preserve zoom anchor using scroll ratio around the event point.
  - Rationale: Users expect the point under the cursor to remain visible when zooming. We can calculate the anchor from scroll offsets before the scale change and restore it on the next animation frame.
  - Alternative considered: Always preserve top-left or current page. That is simpler but feels jumpy for reading formulas and tables.

## Risks / Trade-offs

- Large zoom levels can render big canvases and cost memory -> Cap zoom at 400% and keep fit-to-width reset available.
- Native PDF fallback cannot be controlled by the app -> Keep direct PDF opening available and disable app-specific zoom controls when fallback is active.
- Re-rendering pages during rapid pinch gestures can be heavy -> Clamp and round zoom values, and use modest wheel sensitivity.
