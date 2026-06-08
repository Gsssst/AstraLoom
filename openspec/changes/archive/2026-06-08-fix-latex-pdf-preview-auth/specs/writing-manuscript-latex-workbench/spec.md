## MODIFIED Requirements

### Requirement: LaTeX Preview Checks Are Available
The system SHALL provide compile/preview checks for the active section and assembled manuscript.

#### Scenario: Authenticated PDF preview route
- **WHEN** a logged-in user receives a LaTeX preview response with a PDF preview URL
- **THEN** the frontend loads the PDF using authenticated API credentials
- **AND** displays the compiled PDF in the preview panel instead of a raw 401 error response.

#### Scenario: PDF preview load fails
- **WHEN** the preview PDF URL cannot be loaded
- **THEN** the compile diagnostics remain visible
- **AND** the PDF preview panel shows a clear load failure message.
