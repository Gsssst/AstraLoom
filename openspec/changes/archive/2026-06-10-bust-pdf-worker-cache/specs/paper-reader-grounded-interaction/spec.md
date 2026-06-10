## ADDED Requirements

### Requirement: PDF worker cache is safely invalidated
The paper PDF reader SHALL avoid stale cached pdf.js worker module responses after deployment fixes.

#### Scenario: Browser imports the worker module
- **WHEN** the reader configures the pdf.js worker source
- **THEN** the worker URL includes an application-controlled version query
- **AND** pdf.js imports the versioned worker URL.

#### Scenario: Production serves the worker asset
- **WHEN** the browser requests a bundled `pdf.worker.min-*.mjs` asset
- **THEN** the production frontend server returns it as JavaScript
- **AND** uses a revalidation cache policy rather than one-year immutable caching.
