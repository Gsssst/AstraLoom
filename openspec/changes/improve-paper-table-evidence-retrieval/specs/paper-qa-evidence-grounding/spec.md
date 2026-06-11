## MODIFIED Requirements

### Requirement: Evidence-Backed Paper Q&A

Paper-page AI Q&A SHALL provide structured evidence references for current-paper answers whenever relevant chunks are available. For table-like questions, Paper-page AI Q&A SHALL include relevant table or caption evidence when structured PDF metadata contains such evidence, even when section-first retrieval is active.

#### Scenario: Answer has current-paper evidence

- **GIVEN** a paper has parsed full text
- **WHEN** the user asks a paper-specific question
- **THEN** the stream metadata includes current-paper evidence references with snippets, relevance scores, sections, and page numbers when available.

#### Scenario: Table question has structured evidence

- **GIVEN** a paper has structured PDF metadata with table or caption blocks
- **WHEN** the user asks about tables, benchmarks, baselines, metrics, rewards, ablations, or results
- **THEN** the AI context includes relevant table or caption evidence alongside text evidence
- **AND** the stream metadata identifies those references with evidence type and page number when available

### Requirement: Section-First Retrieval

Paper Q&A SHALL prioritize requested sections for Introduction, Method, and Experiment questions. Section-first retrieval SHALL merge relevant structured table/caption evidence back into the final evidence set when the question is table-like.

#### Scenario: User asks about Introduction

- **GIVEN** the full text contains an Introduction section
- **WHEN** the user asks to explain the Introduction
- **THEN** retrieved evidence comes from the Introduction section before falling back to document-wide chunks.

#### Scenario: Requested section is unavailable

- **GIVEN** the full text does not contain the requested section
- **WHEN** the user asks about that section
- **THEN** retrieval falls back to document-wide chunks.

#### Scenario: User asks about experiment tables

- **GIVEN** the full text contains an Experiment section
- **AND** structured PDF metadata contains relevant tables
- **WHEN** the user asks about experiment table results or benchmarks
- **THEN** retrieval includes both experiment text and relevant structured table/caption evidence
