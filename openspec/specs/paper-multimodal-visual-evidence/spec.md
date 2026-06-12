# paper-multimodal-visual-evidence Specification

## Purpose
TBD - created by archiving change add-multimodal-paper-figure-table-qa. Update Purpose after archive.
## Requirements
### Requirement: PDF Visual Asset Extraction
The system SHALL extract bounded visual assets from a paper PDF, including page previews and detected figure/table regions when available.

#### Scenario: Extract visual assets for a PDF paper
- **WHEN** a paper has a local or cacheable PDF and visual extraction is triggered
- **THEN** the system stores visual asset metadata with page number, asset kind, image path, optional bbox, optional caption, source parser, and extraction timestamp
- **AND** the extraction is bounded by configured page and asset limits.

### Requirement: Optional Visual Summaries
The system SHALL generate visual summaries for extracted assets when an image-capable model/provider is configured, and SHALL preserve unsummarized assets when no vision model is available.

#### Scenario: Vision model is unavailable
- **WHEN** visual assets exist but no image-capable model/provider is configured
- **THEN** the system keeps the visual assets usable as references
- **AND** marks summary status as missing rather than failing paper processing.

#### Scenario: Vision model summarizes an asset
- **WHEN** an extracted visual asset is selected for summarization
- **THEN** the system stores a concise visual summary, key facts, confidence metadata, and the model/provider used.

### Requirement: Visual Evidence Retrieval Lane
Paper Q&A SHALL route figure, chart, architecture, method, and experiment questions through a visual evidence lane when visual assets or summaries are available.

#### Scenario: User asks about a figure or chart
- **WHEN** a paper has visual assets and the question mentions figures, charts, architecture diagrams, methods, or experiments
- **THEN** retrieved evidence includes relevant visual asset summaries or visual packs in addition to text/table evidence.

### Requirement: Visual Evidence References
Paper Q&A SHALL expose visual evidence references with enough metadata for the frontend to display, preview, and navigate them.

#### Scenario: Answer includes visual evidence
- **WHEN** a paper Q&A response uses a visual asset
- **THEN** the response metadata includes the asset id, evidence type, page number, optional bbox, caption, thumbnail or image path, visual summary snippet, and parser/source metadata
- **AND** figure/table visual references prefer focused crop assets over full-page images when crop metadata is available.

### Requirement: Visual Coverage Transparency
The system SHALL disclose when a paper-specific answer is based only on text/table extraction and visual analysis is unavailable.

#### Scenario: Visual evidence is needed but missing
- **WHEN** the user asks a figure/chart/method/experiment question and the paper has no visual assets or summaries
- **THEN** the answer context instructs the model to explicitly say that visual evidence is unavailable and avoid claiming details from unseen figures.
