## Why

Current paper Q&A and chat retrieval can use full text, captions, and table markdown, but it cannot inspect the actual pixels of figures, charts, architecture diagrams, or scanned table regions. This makes method and experiment analysis brittle because many paper claims live only in visual assets.

Recent PDF parsing work improved structured text/table evidence, but the remaining gap is multimodal evidence: extracting visual assets, describing them with a vision model when available, and routing figure/table questions to those assets.

## What Changes

- Add a paper visual-asset layer that extracts page previews and likely figure/table regions from PDFs with page, bbox, caption, image path, and metadata.
- Add optional vision summarization for extracted visual assets so the existing RAG pipeline can retrieve visual summaries without always sending images to the model.
- Extend paper Q&A evidence retrieval with visual evidence lanes for figure, chart, architecture, and experiment questions.
- Expose visual evidence references in paper Q&A metadata so the frontend can show Figure/Table/Page evidence cards.
- Add maintenance/status signals showing whether a paper has visual assets, visual summaries, and whether answers are text-only or multimodal-grounded.
- Keep ColPali/Byaldi-style visual page retrieval as a later optional backend, not a hard dependency for this first deliverable.

## Capabilities

### New Capabilities

- `paper-multimodal-visual-evidence`: Extract, cache, summarize, retrieve, and cite PDF page/figure/table visual assets for paper Q&A.

### Modified Capabilities

- `paper-qa-evidence-grounding`: Paper Q&A evidence references SHALL include visual evidence references when figure/table visual assets are available and relevant.
- `knowledge-base-retrieval-maintenance`: Maintenance SHALL surface papers missing visual assets or summaries when they are needed for method/experiment Q&A.

## Impact

- Backend PDF services: visual extraction, metadata persistence, optional VLM summaries.
- Backend retrieval: visual evidence candidates and multimodal routing for paper Q&A.
- Backend APIs: parse/status fields and maintenance actions for visual evidence.
- Frontend paper detail/Q&A: visual evidence cards and clearer “text-only vs visual-grounded” warnings.
- Configuration: optional visual extraction/summarization settings; no mandatory GPU dependency.
