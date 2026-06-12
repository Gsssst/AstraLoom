## MODIFIED Requirements

### Requirement: Visual Evidence Retrieval Lane
Paper Q&A SHALL route figure, chart, architecture, method, table, and experiment questions through a visual evidence lane when ready visual assets, visual summaries, OCR text, or visual table markdown are available, and broad experiment/table questions SHALL include all ready visual table evidence within budget.

#### Scenario: User asks about a figure or chart
- **WHEN** a paper has ready visual evidence and the question mentions figures, charts, architecture diagrams, methods, or experiments
- **THEN** retrieved evidence includes relevant visual evidence summaries, OCR text, or visual packs in addition to text/table evidence.

#### Scenario: User asks about experimental table results
- **WHEN** a paper has ready visual table evidence or crop-level table OCR
- **THEN** retrieved evidence includes table markdown, table caption, page number, parser source, and confidence metadata before relying on surrounding text alone
- **AND** broad experiment/result/table-analysis questions include all ready visual table evidence within the configured evidence budget instead of selecting only top-k visual table items.

### Requirement: Visual Coverage Transparency
The system SHALL disclose when a paper-specific answer is based only on text/table extraction and visual analysis is unavailable, stale, still processing, or incomplete for the requested detail.

#### Scenario: Visual evidence is needed but missing
- **WHEN** the user asks a figure/chart/method/experiment question and the paper has no ready visual evidence
- **THEN** the answer context instructs the model to explicitly say that visual evidence is unavailable or not ready and avoid claiming details from unseen figures.

#### Scenario: Visual extraction failed
- **WHEN** visual evidence extraction has a recorded failure
- **THEN** the system exposes the failure state to maintenance users and instructs Q&A to answer only from available non-visual evidence.

#### Scenario: Visual table evidence is partial
- **WHEN** a broad experiment question has visual table references but lacks OCR or table markdown for some tables
- **THEN** the answer context instructs the model to distinguish available table captions or summaries from missing exact cell values.
