## MODIFIED Requirements

### Requirement: Evidence-Backed Paper Q&A
Paper-page AI Q&A SHALL provide structured evidence references for current-paper answers whenever relevant chunks, tables, or visual assets are available.

#### Scenario: Answer has current-paper evidence

- **GIVEN** a paper has parsed full text, structured tables, or visual assets
- **WHEN** the user asks a paper-specific question
- **THEN** the stream metadata includes current-paper evidence references with snippets, relevance scores, evidence types, sections, and page numbers when available
- **AND** visual references include asset metadata when the answer uses figure/table/page visual evidence.

## ADDED Requirements

### Requirement: Multimodal Evidence Routing
Paper Q&A SHALL prefer visual evidence alongside text/table evidence for figure, chart, architecture, method, and experiment questions.

#### Scenario: User asks about method diagram
- **GIVEN** a paper has extracted visual assets or visual summaries
- **WHEN** the user asks about the method architecture, figure, chart, or experimental visualization
- **THEN** the retrieved evidence includes visual candidates before falling back to text-only evidence.

### Requirement: Visual Evidence Insufficiency Disclosure
Paper Q&A SHALL clearly disclose when visual evidence is missing for a question that appears to require reading figures or charts.

#### Scenario: Figure question has no visual evidence
- **GIVEN** a paper has no visual assets or no visual summaries
- **WHEN** the user asks about a figure, chart, architecture diagram, or plot
- **THEN** the system prompt instructs the model to say that visual evidence is unavailable instead of inferring unseen figure details from surrounding text alone.
