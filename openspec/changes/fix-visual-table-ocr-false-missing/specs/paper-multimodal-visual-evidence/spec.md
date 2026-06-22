## ADDED Requirements

### Requirement: Visual table OCR status uses corrected evidence type
The system SHALL compute visual evidence table OCR readiness from the effective evidence type after parser metadata and vision-model corrections are applied.

#### Scenario: Vision model corrects parser table candidate to figure
- **WHEN** a cached visual evidence item has original kind `table`
- **AND** its vision elements identify the visible asset as a `figure` with no table element
- **THEN** the visual evidence status SHALL NOT count that item as missing table OCR.

#### Scenario: Vision model reports text page with no visible table
- **WHEN** a cached visual evidence item has original kind `table`
- **AND** its vision elements identify the visible asset as `text` with no table element
- **THEN** the visual evidence status SHALL NOT count that item as missing table OCR.

#### Scenario: True table without markdown remains incomplete
- **WHEN** a cached visual evidence item is effectively a table
- **AND** it has no table markdown
- **THEN** the visual evidence status SHALL count that item as missing table OCR.
