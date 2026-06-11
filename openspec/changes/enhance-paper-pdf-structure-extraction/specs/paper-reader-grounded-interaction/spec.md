## ADDED Requirements

### Requirement: Paper AI retrieves structured PDF evidence
The paper AI backend SHALL include page-aware structured PDF evidence blocks from detected tables, captions, and visual placeholders when building retrieval context for paper questions. The backend SHALL preserve plain-text fallback behavior when structured extraction is unavailable.

#### Scenario: Question targets table content
- **WHEN** a paper PDF extraction contains a table with experiment metrics or ablation values
- **THEN** paper AI retrieval includes a table evidence block converted to Markdown with its PDF page number

#### Scenario: Question targets figure content
- **WHEN** a paper PDF extraction contains figure or table captions
- **THEN** paper AI retrieval includes caption evidence with its PDF page number
- **AND** visual placeholders disclose image presence without claiming pixel-level interpretation

#### Scenario: Structured extraction is unavailable
- **WHEN** structured PDF parsing fails or no structured blocks are found
- **THEN** paper AI retrieval continues to use the existing plain extracted text and insufficient-evidence warning behavior

### Requirement: Structured PDF extraction is cached with paper metadata
The paper AI backend SHALL persist a bounded structured PDF extraction summary in paper metadata after successful PDF parsing and SHALL reuse that summary on later paper questions when the source PDF path has not changed.

#### Scenario: Full text parsing succeeds
- **WHEN** a paper PDF is downloaded and parsed into full text
- **THEN** the backend stores structured PDF metadata containing page count, table count, visual block count, and structured Markdown snippets

#### Scenario: Existing PDF path has cached structured content
- **WHEN** a later paper question is asked for the same PDF path
- **THEN** the backend reuses cached structured PDF metadata instead of reparsing the PDF
