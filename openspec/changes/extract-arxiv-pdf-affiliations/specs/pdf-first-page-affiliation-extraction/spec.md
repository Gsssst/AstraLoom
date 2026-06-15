## ADDED Requirements

### Requirement: Extract affiliations from arXiv PDF first pages
The scholarly discovery service SHALL be able to extract institution evidence from the first page of arXiv PDFs during arXiv-first enriched discovery.

#### Scenario: PDF first page has institution lines
- **WHEN** an arXiv candidate has a PDF URL and the first page contains visible institution-like text
- **THEN** discovery includes extracted institutions in candidate metadata
- **AND** records provenance as `pdf_first_page`
- **AND** includes a bounded evidence snippet from the first page.

#### Scenario: PDF parsing fails
- **WHEN** the PDF cannot be downloaded or parsed within configured bounds
- **THEN** discovery keeps the candidate
- **AND** does not fabricate institutions.

#### Scenario: Provider institutions already exist
- **WHEN** OpenAlex or another provider has institution metadata and PDF extraction also finds institutions
- **THEN** discovery merges non-duplicate institutions
- **AND** keeps provenance for provider and PDF-derived fields.
