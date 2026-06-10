## ADDED Requirements

### Requirement: PDF reader falls back to native preview
The paper PDF reader SHALL provide a browser-native PDF preview fallback when pdf.js cannot render a valid proxied PDF.

#### Scenario: pdf.js loading times out
- **WHEN** pdf.js does not report success or failure within the loading timeout
- **THEN** the reader switches to native PDF preview using the same resolved PDF URL
- **AND** shows a notice that page-aware selection is unavailable in fallback mode.

#### Scenario: pdf.js reports a load error
- **WHEN** pdf.js reports a document load error
- **THEN** the reader switches to native PDF preview
- **AND** preserves a direct link to open the PDF.

#### Scenario: User retries the enhanced reader
- **WHEN** the native preview fallback is shown
- **THEN** the user can retry the enhanced pdf.js reader without leaving the paper page.
