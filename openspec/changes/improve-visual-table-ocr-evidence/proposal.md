## Why

Paper Q&A can still report incomplete experimental tables even when the PDF page image clearly contains the full table. Investigation on `Towards One-to-Many Temporal Grounding` shows that `pdfplumber` stores low-fidelity markdown for Table 4 and misses Table 10/13 rows, while generated page images are clear enough for model OCR but no OCR call is currently made.

## What Changes

- Enrich all weak table-like visual evidence with model OCR using the system-configured model, producing structured markdown, OCR text, key facts, uncertainty notes, and model metadata.
- Use already-rendered page/crop assets as the OCR input without requiring a separate vision-model configuration state.
- Prefer OCR-enhanced visual table markdown in paper Q&A evidence when structured tables are low fidelity or incomplete.
- Classify Chinese broad experiment-analysis questions such as "实验分析" and "实验结果分析" as complete experiment evidence requests, not narrow table lookup.
- Add regression coverage for OMTG-style tables where page images are available but `pdfplumber` output has generic headers, missing rows, or caption-only tables.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `document-visual-evidence-pipeline`: Visual table evidence should use bounded system-model OCR to produce structured table markdown when parser text is missing or low fidelity.
- `paper-qa-evidence-grounding`: Broad experiment-analysis questions should retrieve all available experiment tables and OCR-enhanced visual table evidence within budget.

## Impact

- Backend: visual evidence enrichment, OCR prompt/result normalization, paper evidence planner, and table evidence scoring.
- Frontend/API: no new UI state; existing visual evidence status and references expose improved markdown/metadata.
- Runtime: table OCR runs during visual evidence extraction, stores results for later Q&A, and can still be capped by deployment configuration when needed.
