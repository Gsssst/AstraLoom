## MODIFIED Requirements

### Requirement: Paper full text loading uses available PDF parsers
The paper AI backend SHALL extract and persist paper full text with an installed PDF parser before answering section-specific questions. Concurrent requests for the same missing full text SHALL share one loading task, and timed-out foreground waits SHALL allow that task to finish in the background.

#### Scenario: Paper detail preload and question overlap
- **WHEN** paper detail preload and a paper question request full text for the same paper at the same time
- **THEN** the backend performs one shared PDF loading task and persists the extracted text

#### Scenario: Primary PDF parser is available
- **WHEN** a downloaded PDF contains extractable text and `pdfplumber` is installed
- **THEN** the backend extracts full text without requiring optional `fitz`

#### Scenario: Structured parser quality is reported
- **WHEN** structured PDF parsing completes for a paper with table blocks
- **THEN** the parser status includes table quality metadata
- **AND** low-fidelity table extraction is distinguishable from high-quality structured parsing

#### Scenario: Advanced parser is available
- **WHEN** a configured advanced parser such as Docling or a command parser returns usable table blocks
- **THEN** the backend persists those blocks as structured evidence before falling back to lightweight table extraction
