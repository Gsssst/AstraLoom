## ADDED Requirements

### Requirement: Paper detail exposes structured PDF parse status
The paper detail API and page SHALL expose structured PDF parse readiness, including parser source, page count, structured block counts, parsed timestamp, and latest parse error when available.

#### Scenario: Structured parse metadata exists
- **WHEN** a paper has cached structured PDF metadata
- **THEN** the paper detail response includes parse status marked ready
- **AND** the paper detail page shows parser source and counts for table, caption, visual, OCR, formula, and total blocks

#### Scenario: Structured parse metadata is missing
- **WHEN** a paper has no structured PDF metadata
- **THEN** the paper detail page shows that structured parsing is not ready
- **AND** paper Q&A remains usable through existing text and abstract fallback behavior

### Requirement: Admin can rerun structured PDF parsing
The paper AI backend SHALL provide an admin-only endpoint to force structured PDF parsing for a paper and SHALL persist the new parse status or failure metadata.

#### Scenario: Admin reruns parse successfully
- **WHEN** an admin triggers structured PDF reparse for a paper with an available PDF
- **THEN** the backend refreshes structured parse metadata
- **AND** returns parser source, block counts, and parsed timestamp

#### Scenario: Reparse fails
- **WHEN** structured PDF reparse fails
- **THEN** the backend records latest parse error metadata
- **AND** returns a visible failure response without deleting existing full text
