## ADDED Requirements

### Requirement: Production PDF worker assets are served as JavaScript modules
The production frontend server SHALL serve pdf.js worker `.mjs` assets with a JavaScript MIME type so browsers can dynamically import the worker.

#### Scenario: Browser loads the bundled pdf.js worker
- **WHEN** the production build emits a hashed `pdf.worker.min-*.mjs` asset under `/assets/`
- **THEN** the frontend server returns the worker with a JavaScript MIME type
- **AND** pdf.js can import the worker instead of falling back to a failed fake worker setup.
