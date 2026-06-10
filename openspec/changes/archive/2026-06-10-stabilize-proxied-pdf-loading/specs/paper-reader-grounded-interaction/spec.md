## ADDED Requirements

### Requirement: Proxied PDF loading avoids unresolved spinner states
The paper PDF reader SHALL use a conservative full-file pdf.js loading mode for same-origin proxied PDFs and SHALL surface a visible diagnostic if loading does not resolve within a bounded time.

#### Scenario: PDF is served through the application proxy
- **WHEN** the paper reader opens a PDF URL resolved against the current application origin
- **THEN** the PDF document descriptor disables range loading
- **AND** disables streaming and auto-fetch behavior.

#### Scenario: Browser loading remains unresolved
- **WHEN** pdf.js does not report success or failure within the loading timeout
- **THEN** the reader shows a PDF loading timeout diagnostic
- **AND** provides a direct link to open the PDF endpoint.
