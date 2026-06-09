## ADDED Requirements

### Requirement: Production PDF loading is diagnosable
The paper PDF reader SHALL use a production-safe PDF file descriptor and SHALL show an actionable frontend diagnostic when pdf.js fails to load a PDF.

#### Scenario: Backend PDF proxy returns a valid PDF
- **WHEN** a paper has an arXiv-backed PDF proxy URL
- **THEN** the frontend resolves the URL against the current origin
- **AND** passes an explicit URL descriptor to the PDF document loader.

#### Scenario: PDF loading fails in the browser
- **WHEN** pdf.js fails to load or parse the configured PDF URL
- **THEN** the PDF panel shows a concise error message with the failing URL context
- **AND** the reader does not leave only the generic pdf.js fallback text visible.
