## ADDED Requirements

### Requirement: Docling parser adapter is optional at deployment
Production deployments SHALL be able to enable the Docling parser adapter through configuration when Docling is installed, while deployments without Docling SHALL continue to run with the lightweight parser.

#### Scenario: Deployment enables Docling
- **WHEN** an operator installs Docling in the backend environment
- **AND** sets `PDF_STRUCTURED_PARSER_BACKEND=docling`
- **THEN** the backend uses the Docling adapter for structured PDF parsing
- **AND** uses configured HuggingFace mirror/cache environment variables during conversion

#### Scenario: Deployment does not install Docling
- **WHEN** Docling is not installed in the backend environment
- **THEN** application startup and paper parsing do not require the Docling package
