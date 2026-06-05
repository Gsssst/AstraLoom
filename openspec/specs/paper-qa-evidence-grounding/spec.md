# paper-qa-evidence-grounding Specification

## Purpose
TBD - created by archiving change paper-qa-evidence-grounding. Update Purpose after archive.
## Requirements
### Requirement: Evidence-Backed Paper Q&A

Paper-page AI Q&A SHALL provide structured evidence references for current-paper answers whenever relevant chunks are available.

#### Scenario: Answer has current-paper evidence

- **GIVEN** a paper has parsed full text
- **WHEN** the user asks a paper-specific question
- **THEN** the stream metadata includes current-paper evidence references with snippets, relevance scores, sections, and page numbers when available.

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

