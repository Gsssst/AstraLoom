# paper-qa-evidence-grounding Specification

## Purpose
TBD - created by archiving change paper-qa-evidence-grounding. Update Purpose after archive.
## Requirements
### Requirement: Evidence-Backed Paper Q&A
Paper-page AI Q&A SHALL provide structured evidence references for current-paper answers whenever relevant chunks, tables, or ready visual evidence are available.

#### Scenario: Answer has current-paper evidence
- **GIVEN** a paper has parsed full text, structured tables, captions, OCR, or ready visual evidence
- **WHEN** the user asks a paper-specific question
- **THEN** the stream metadata includes current-paper evidence references with snippets, relevance scores, evidence types, sections, and page numbers when available
- **AND** visual references include asset metadata, bbox, caption, parser source, and confidence when the answer uses figure, chart, table crop, or page visual evidence.

### Requirement: Section-First Retrieval

Paper Q&A SHALL prioritize requested sections for Introduction, Method, and Experiment questions.

#### Scenario: User asks about Introduction

- **GIVEN** the full text contains an Introduction section
- **WHEN** the user asks to explain the Introduction
- **THEN** retrieved evidence comes from the Introduction section before falling back to document-wide chunks.

### Requirement: Evidence Insufficiency Disclosure

Paper Q&A SHALL clearly disclose when evidence is insufficient.

#### Scenario: No supporting evidence is found

- **GIVEN** the paper lacks full text or retrieval returns no relevant chunks
- **WHEN** the AI builds its answer context
- **THEN** the system prompt instructs the model to say "当前论文内容不足" instead of inferring unsupported details from the abstract.

### Requirement: Clickable PDF Evidence Navigation

The frontend SHALL let users jump from a paper Q&A evidence reference to the referenced PDF page when a page number is available.

#### Scenario: User clicks evidence reference

- **GIVEN** a streamed answer has a current-paper evidence reference with a page number
- **WHEN** the user clicks the reference chip
- **THEN** the PDF panel opens and navigates to that page.

### Requirement: Multimodal Evidence Routing
Paper Q&A SHALL prefer ready visual evidence alongside text/table evidence for figure, chart, architecture, method, and experiment questions.

#### Scenario: User asks about method diagram
- **GIVEN** a paper has extracted visual assets, OCR text, table crop markdown, or visual summaries marked ready
- **WHEN** the user asks about the method architecture, figure, chart, or experimental visualization
- **THEN** the retrieved evidence includes visual candidates before falling back to text-only evidence.

#### Scenario: User asks about experimental results
- **GIVEN** a paper has ready structured tables or visual table evidence
- **WHEN** the user asks about experimental results, ablations, baselines, charts, or metrics
- **THEN** the retrieved evidence includes table packs, visual table markdown, captions, and page-aware context before general full-text chunks.

### Requirement: Visual Evidence Insufficiency Disclosure
Paper Q&A SHALL clearly disclose when visual evidence is missing, stale, failed, or still processing for a question that appears to require reading figures or charts.

#### Scenario: Figure question has no visual evidence
- **GIVEN** a paper has no ready visual assets, visual OCR, or visual summaries
- **WHEN** the user asks about a figure, chart, architecture diagram, or plot
- **THEN** the system prompt instructs the model to say that visual evidence is unavailable instead of inferring unseen figure details from surrounding text alone.

#### Scenario: Visual evidence is processing
- **GIVEN** a paper has a visual evidence job queued or running
- **WHEN** the user asks a visual question
- **THEN** the system prompt instructs the model to state that visual evidence is still processing and answer only from currently available text/table evidence.

