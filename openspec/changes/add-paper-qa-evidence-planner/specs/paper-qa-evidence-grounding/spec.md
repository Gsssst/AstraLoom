## MODIFIED Requirements

### Requirement: Evidence-Backed Paper Q&A
Paper-page AI Q&A SHALL provide structured evidence references and evidence-plan metadata for current-paper answers whenever relevant chunks, tables, or ready visual evidence are available.

#### Scenario: Answer has current-paper evidence
- **GIVEN** a paper has parsed full text, structured tables, captions, OCR, or ready visual evidence
- **WHEN** the user asks a paper-specific question
- **THEN** the stream metadata includes current-paper evidence references with snippets, relevance scores, evidence types, sections, and page numbers when available
- **AND** visual references include asset metadata, bbox, caption, parser source, and confidence when the answer uses figure, chart, table crop, or page visual evidence
- **AND** the response evidence metadata includes the selected evidence plan intent and strategy.

### Requirement: Section-First Retrieval

Paper Q&A SHALL prioritize requested sections for Introduction, Method, and Experiment questions, and SHALL use complete bounded evidence packs for broad section-analysis questions.

#### Scenario: User asks about Introduction

- **GIVEN** the full text contains an Introduction section
- **WHEN** the user asks to explain the Introduction
- **THEN** retrieved evidence comes from the Introduction section before falling back to document-wide chunks.

#### Scenario: User asks to analyze experiments
- **GIVEN** the paper has experiment or evaluation sections and structured table or visual table evidence
- **WHEN** the user asks to analyze experiments, results, ablations, baselines, datasets, metrics, or comparisons
- **THEN** retrieved evidence includes a bounded complete experiment evidence pack with experiment-section text, all available structured tables, all ready visual tables, relevant table captions, page numbers, parser source, confidence metadata, and truncation warnings when budget limits apply
- **AND** the system SHALL NOT rely solely on generic top-k chunks for the experiment answer.

### Requirement: Evidence Insufficiency Disclosure

Paper Q&A SHALL clearly disclose the specific missing evidence needed for an answer instead of overusing whole-paper insufficiency language.

#### Scenario: No supporting evidence is found

- **GIVEN** the paper lacks full text or retrieval returns no relevant chunks, tables, captions, OCR, or ready visual evidence
- **WHEN** the AI builds its answer context
- **THEN** the system prompt instructs the model to say "当前论文内容不足" instead of inferring unsupported details from the abstract.

#### Scenario: Partial evidence is found
- **GIVEN** retrieval returns paper evidence but lacks exact table values, visual OCR, or a requested figure detail
- **WHEN** the AI builds its answer context
- **THEN** the system prompt instructs the model to identify the specific missing evidence while still answering from available paper evidence.

### Requirement: Multimodal Evidence Routing
Paper Q&A SHALL prefer ready visual evidence alongside text/table evidence for figure, chart, architecture, method, and experiment questions, and SHALL choose the retrieval strategy from an explicit evidence plan before assembling context.

#### Scenario: User asks about method diagram
- **GIVEN** a paper has extracted visual assets, OCR text, table crop markdown, or visual summaries marked ready
- **WHEN** the user asks about the method architecture, figure, chart, or experimental visualization
- **THEN** the evidence plan chooses a method or visual strategy
- **AND** retrieved evidence includes visual candidates before falling back to text-only evidence.

#### Scenario: User asks about experimental results
- **GIVEN** a paper has ready structured tables or visual table evidence
- **WHEN** the user asks about experimental results, ablations, baselines, charts, or metrics
- **THEN** the evidence plan chooses an experiment-complete strategy
- **AND** retrieved evidence includes table packs, visual table markdown, captions, and page-aware context before general full-text chunks.

