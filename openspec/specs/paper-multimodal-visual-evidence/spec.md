# paper-multimodal-visual-evidence Specification

## Purpose
TBD - created by archiving change add-multimodal-paper-figure-table-qa. Update Purpose after archive.
## Requirements
### Requirement: PDF Visual Asset Extraction
The system SHALL extract bounded visual evidence assets from a paper PDF by using parser-detected page regions, captions, tables, formulas, OCR blocks, and optional crop images when available.

#### Scenario: Extract visual assets for a PDF paper
- **WHEN** a paper has a local or cacheable PDF and visual extraction is triggered
- **THEN** the system stores visual evidence metadata with page number, asset kind, image path when available, optional bbox, optional caption, parser source, confidence, status, and extraction timestamp
- **AND** the extraction is bounded by configured page, asset, crop, and model-call limits.

#### Scenario: Parser locates visual regions
- **WHEN** Docling, MinerU, PaddleOCR/PP-Structure, or a configured command parser returns figure, chart, table, image, OCR, formula, or caption regions
- **THEN** the system normalizes those regions into the shared document visual evidence schema.

### Requirement: Optional Visual Summaries
The system SHALL generate visual summaries or OCR/table markdown for selected evidence crops when an image-capable model/provider is configured, and SHALL preserve unsummarized assets when no vision model is available.

#### Scenario: Vision model is unavailable
- **WHEN** visual assets exist but no image-capable model/provider is configured
- **THEN** the system keeps the visual assets usable as references
- **AND** marks summary or OCR status as missing rather than failing paper processing.

#### Scenario: Vision model summarizes an asset
- **WHEN** an extracted visual crop is selected for summarization or OCR
- **THEN** the system stores concise visual summary, OCR text or table markdown when applicable, key facts, confidence metadata, and the model/provider used.

#### Scenario: Direct whole-PDF model OCR is not configured
- **WHEN** a default visual extraction job runs
- **THEN** the system analyzes selected crops rather than sending the full PDF or every page image to a vision model.

### Requirement: Visual Evidence Retrieval Lane
Paper Q&A SHALL route figure, chart, architecture, method, table, and experiment questions through a visual evidence lane when ready visual assets, visual summaries, OCR text, or visual table markdown are available.

#### Scenario: User asks about a figure or chart
- **WHEN** a paper has ready visual evidence and the question mentions figures, charts, architecture diagrams, methods, or experiments
- **THEN** retrieved evidence includes relevant visual evidence summaries, OCR text, or visual packs in addition to text/table evidence.

#### Scenario: User asks about experimental table results
- **WHEN** a paper has ready visual table evidence or crop-level table OCR
- **THEN** retrieved evidence includes table markdown, table caption, page number, parser source, and confidence metadata before relying on surrounding text alone.

### Requirement: Visual Evidence References
Paper Q&A SHALL expose visual evidence references with enough metadata for the frontend to display, preview, and navigate them.

#### Scenario: Answer includes visual evidence
- **WHEN** a paper Q&A response uses a visual evidence item
- **THEN** the response metadata includes the evidence id, evidence type, page number, optional bbox, caption, thumbnail or image path, visual summary or OCR snippet, parser/source metadata, and confidence
- **AND** figure/table visual references prefer focused crop assets over full-page images when crop metadata is available.

### Requirement: Visual Coverage Transparency
The system SHALL disclose when a paper-specific answer is based only on text/table extraction and visual analysis is unavailable, stale, or still processing.

#### Scenario: Visual evidence is needed but missing
- **WHEN** the user asks a figure/chart/method/experiment question and the paper has no ready visual evidence
- **THEN** the answer context instructs the model to explicitly say that visual evidence is unavailable or not ready and avoid claiming details from unseen figures.

#### Scenario: Visual extraction failed
- **WHEN** visual evidence extraction has a recorded failure
- **THEN** the system exposes the failure state to maintenance users and instructs Q&A to answer only from available non-visual evidence.
