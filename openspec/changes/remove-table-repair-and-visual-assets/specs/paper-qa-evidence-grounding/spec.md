## MODIFIED Requirements

### Requirement: Evidence-Backed Paper Q&A
Paper-page AI Q&A SHALL provide structured evidence references for current-paper answers whenever relevant text chunks or structured tables are available.

#### Scenario: Answer has current-paper evidence

- **GIVEN** a paper has parsed full text or structured tables
- **WHEN** the user asks a paper-specific question
- **THEN** the stream metadata includes current-paper evidence references with snippets, relevance scores, evidence types, sections, and page numbers when available.

## REMOVED Requirements

### Requirement: Multimodal Evidence Routing
**Reason**: The current visual asset evidence implementation is being discarded.
**Migration**: Paper Q&A uses text and structured table evidence only until a replacement visual evidence strategy is proposed.

### Requirement: Visual Evidence Insufficiency Disclosure
**Reason**: The product will no longer advertise visual evidence coverage in the reset baseline.
**Migration**: Remove visual-missing prompts and UI messages tied to the discarded visual asset runtime.
