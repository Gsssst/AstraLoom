## ADDED Requirements

### Requirement: High-Fidelity Table Evidence
Paper Q&A SHALL prefer high-fidelity repaired table evidence when exact table values are requested and repaired table data is available.

#### Scenario: Repaired table cells are used for value questions
- **WHEN** a user asks for exact table values, metrics, baselines, or per-task results
- **AND** a table block has repaired cell metadata
- **THEN** the evidence bundle SHALL include the repaired table body with cell-derived Markdown
- **AND** the evidence reference metadata SHALL expose the repair source and quality flags.

#### Scenario: Low-quality table blocks are disclosed
- **WHEN** a table-like answer relies on table blocks marked low quality
- **THEN** the evidence metadata SHALL expose low-quality flags
- **AND** the system SHALL be able to trigger or recommend table repair rather than only asking the user to rephrase.

### Requirement: Cell-Level Table Preservation
Structured table evidence SHALL preserve cell-level table structure when a parser provides it.

#### Scenario: Parser returns cells
- **WHEN** a structured parser returns headers, rows, cells, caption, confidence, page, or bounding boxes
- **THEN** the normalized structured block SHALL preserve those fields in metadata
- **AND** the table Markdown SHALL be regenerated from cells when that produces a cleaner table.

#### Scenario: Parser returns HTML table
- **WHEN** a structured parser returns an HTML table
- **THEN** the normalized structured block SHALL extract rows and cells from the HTML table when possible
- **AND** store the derived cells in metadata.
