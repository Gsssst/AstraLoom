## Context

The enhanced PDF pane renders pages with `react-pdf`. The previous global zoom implementation multiplied `pageWidth` and passed the result to `<Page width={...}>`. This keeps the canvas crisp but makes each zoom step a pdf.js render operation. During fast wheel or touchpad gestures, users see a white repaint gap.

Mature PDF viewers avoid coupling every gesture event to full page rendering. They keep the current rendered page visible and apply an immediate viewport transform while the interaction is happening.

## Goals / Non-Goals

**Goals:**
- Make PDF zoom feel immediate and continuous.
- Avoid white blanking while users pinch or use modifier-wheel zoom.
- Keep the same zoom controls and bounds.
- Preserve page layout, text selection, and evidence jump behavior.

**Non-Goals:**
- Replacing `react-pdf` or pdf.js.
- Implementing a multi-resolution tile renderer.
- Adding a local magnifier.

## Decisions

- Keep `<Page width={pageWidth}>` stable during zoom and apply `transform: scale(zoomScale)` to an inner page shell.
  - Rationale: CSS transforms reuse the already rendered canvas/text/annotation DOM, so the page remains visible during zoom.
  - Trade-off: Canvas pixels can look softer at high zoom than a fresh high-resolution render. The interaction quality is more important for this fix.

- Reserve scaled layout space with per-page aspect ratios.
  - Rationale: CSS transforms do not affect normal document flow. The outer page wrapper needs scaled width and height so pages do not overlap and scrolling remains natural.

- Scroll evidence hits using transformed client rectangles.
  - Rationale: `scrollIntoView` uses layout geometry that can be misleading under transforms. Client rectangles reflect what users actually see.

## Risks / Trade-offs

- High zoom can be softer because it scales the existing canvas -> Keep the 400% cap and use this as the stable interaction baseline; a later idle high-resolution rerender can be added if needed.
- Page aspect ratios load asynchronously -> Use an A4-like fallback ratio until pdf.js reports each page viewport.
