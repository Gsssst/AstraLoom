## ADDED Requirements

### Requirement: Paper AI can use an advanced PDF parser backend
The paper AI backend SHALL support a configurable advanced structured PDF parser backend that can produce table, caption, formula, OCR, and visual-description evidence blocks, and SHALL fall back to the lightweight installed parser when the advanced backend is disabled or fails.

#### Scenario: Advanced parser returns structured JSON
- **WHEN** an operator configures an advanced parser command and it returns valid structured JSON for a PDF
- **THEN** the backend normalizes the returned blocks into paper evidence with type, text, page number, parser source, and metadata
- **AND** paper Q&A retrieval can use those blocks alongside plain text

#### Scenario: Advanced parser fails
- **WHEN** the configured advanced parser command times out, exits non-zero, or returns invalid JSON
- **THEN** the backend logs the parser failure
- **AND** falls back to lightweight PDF structured extraction instead of failing the paper question

#### Scenario: Advanced parser is disabled
- **WHEN** no advanced parser command is configured
- **THEN** the backend uses the existing lightweight structured extraction behavior
