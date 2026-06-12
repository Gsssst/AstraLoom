## MODIFIED Requirements

### Requirement: Visual Asset Extraction Runtime

Paper Q&A SHALL have an operational local runtime for extracting visual assets from PDFs when visual asset extraction is enabled.

#### Scenario: Runtime can render PDF visual assets

- **GIVEN** visual asset extraction is enabled
- **AND** a paper has a readable local PDF
- **WHEN** the backend extracts visual assets for the paper
- **THEN** it renders at least one bounded page image asset
- **AND** it persists asset metadata including asset id, page, kind, image path, and parser
- **AND** the referenced image file exists on disk

#### Scenario: Runtime readiness is diagnosable

- **WHEN** parser/runtime health is requested
- **THEN** the health payload reports whether `fitz`/PyMuPDF is available
- **AND** visual extraction failures include a clear dependency error when PyMuPDF is missing.
