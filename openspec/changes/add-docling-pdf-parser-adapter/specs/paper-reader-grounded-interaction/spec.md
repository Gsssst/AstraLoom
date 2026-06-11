## ADDED Requirements

### Requirement: Paper AI can use Docling as an optional parser backend
The paper AI backend SHALL support `docling` as an optional structured PDF parser backend value. When Docling is installed and configured, the backend SHALL normalize Docling document output into paper evidence blocks; when Docling is unavailable or fails, it SHALL fall back to lightweight structured extraction.

#### Scenario: Docling backend returns document content
- **WHEN** `PDF_STRUCTURED_PARSER_BACKEND` is set to `docling`
- **AND** Docling converts the PDF successfully
- **THEN** the backend stores normalized Docling evidence blocks with parser source `docling`
- **AND** paper Q&A retrieval can use those blocks

#### Scenario: Docling package is unavailable
- **WHEN** `PDF_STRUCTURED_PARSER_BACKEND` is set to `docling`
- **AND** the Docling package is not installed
- **THEN** the backend falls back to lightweight structured extraction instead of failing the paper question
