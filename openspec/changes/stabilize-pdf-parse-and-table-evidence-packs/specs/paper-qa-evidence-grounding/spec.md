## MODIFIED Requirements

### Requirement: Evidence-Backed Paper Q&A
Paper-page AI Q&A SHALL provide structured evidence references for current-paper answers whenever relevant chunks are available. For table-like questions, Paper-page AI Q&A SHALL include grouped table evidence when structured PDF metadata contains such evidence.

#### Scenario: Answer has current-paper evidence
- **GIVEN** a paper has parsed full text
- **WHEN** the user asks a paper-specific question
- **THEN** the stream metadata includes current-paper evidence references with snippets, relevance scores, sections, and page numbers when available

#### Scenario: Table question uses adaptive evidence budget
- **GIVEN** a paper has structured PDF metadata with table or caption blocks
- **WHEN** the user asks about tables, benchmarks, baselines, metrics, rewards, ablations, or results
- **THEN** the AI context includes more than the default compact evidence budget when relevant evidence is available
- **AND** the evidence is still bounded to avoid unbounded prompt growth

#### Scenario: Table evidence is grouped with context
- **GIVEN** a selected structured table block has same-page table captions or page text
- **WHEN** the user asks a table-like question
- **THEN** the AI context includes a table evidence pack containing the selected table and related same-page caption or explanatory text when available
- **AND** the stream metadata identifies the reference with evidence type, parser source, score, snippet, metadata, and PDF page

### Requirement: Section-First Retrieval
Paper Q&A SHALL prioritize requested sections for Introduction, Method, and Experiment questions. Section-first retrieval SHALL merge relevant structured table/caption evidence back into the final evidence set when the question is table-like.

#### Scenario: User asks about experiment tables
- **GIVEN** the full text contains an Experiment section
- **AND** structured PDF metadata contains relevant tables
- **WHEN** the user asks about experiment table results or benchmarks
- **THEN** retrieval includes both experiment text and grouped structured table/caption evidence
