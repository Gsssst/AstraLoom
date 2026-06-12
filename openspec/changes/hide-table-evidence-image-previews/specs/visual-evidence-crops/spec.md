## MODIFIED Requirements

### Requirement: Preview-Ready Visual References
The frontend SHALL display non-table visual evidence references as compact preview cards when an image asset is available and reference details are expanded, and SHALL display table-like evidence references as compact textual references with page navigation.

#### Scenario: Paper Q&A answer includes non-table visual evidence
- **WHEN** a paper Q&A answer includes a figure, chart, architecture, diagram, or page visual evidence reference with an asset id and the user expands references
- **THEN** the UI shows a preview card containing the thumbnail/image, visual kind, page number, confidence, and caption or snippet
- **AND** clicking the card navigates to the referenced PDF page when available.

#### Scenario: Paper Q&A answer includes table visual evidence
- **WHEN** a paper Q&A answer includes a table, visual table, table pack, or table catalog evidence reference with an asset id
- **THEN** the UI does not render an image preview card for that reference
- **AND** the UI still shows a compact textual evidence reference and allows PDF page navigation when a page number is available.

#### Scenario: Evidence has no image preview
- **WHEN** a visual evidence reference has page and caption metadata but no image asset and the user expands references
- **THEN** the UI still shows a compact textual evidence reference and allows PDF page navigation when a page number is available.

### Requirement: Collapsible Paper Q&A References
Paper Q&A answers SHALL keep evidence details collapsed by default while preserving a clear path to inspect references.

#### Scenario: Answer includes references
- **WHEN** a paper Q&A answer includes references or evidence metadata
- **THEN** the UI displays a compact evidence summary with confidence, coverage, and evidence counts
- **AND** preview cards and citation chips are hidden by default.

#### Scenario: User expands references
- **WHEN** the user clicks the reference toggle for a paper Q&A answer
- **THEN** the UI displays the available non-table visual preview cards and compact textual citation references
- **AND** clicking a citation or preview navigates to the referenced PDF page when available.
