## Why

The first multimodal paper Q&A pass exposes visual assets, but figure/table references still often point to full-page renders. Users need more precise, glanceable visual evidence when asking about diagrams, plots, tables, methods, or experiments.

## What Changes

- Add region-cropped visual assets for caption-linked figures and tables, including bbox and crop strategy metadata.
- Preserve page-level visual assets as fallback when a precise crop cannot be produced.
- Show visual evidence references in the paper Q&A UI as compact preview cards with image thumbnails, page, kind, and caption context.
- Keep the implementation dependency-light by using the existing PyMuPDF extraction path and layout heuristics, while leaving room for future layout detectors.

## Capabilities

### New Capabilities

- `visual-evidence-crops`: Figure/table visual evidence region crops and preview metadata.

### Modified Capabilities

- `paper-multimodal-visual-evidence`: Visual evidence references must expose preview-ready region assets rather than only page-level references when available.

## Impact

- Backend: `paper_visual_service` extraction metadata and image paths.
- Frontend: paper detail Q&A reference rendering.
- Tests: backend visual metadata tests and frontend contract tests.
