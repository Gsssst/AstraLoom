## ADDED Requirements

### Requirement: PDF reader initializes a real worker port in production
The paper PDF reader SHALL initialize pdf.js with an explicit module `Worker` port when the browser supports workers, while preserving a worker source fallback.

#### Scenario: Browser supports module workers
- **WHEN** the paper PDF reader module loads in a browser with `Worker` support
- **THEN** it creates a module worker from the bundled pdf.js worker asset
- **AND** assigns it to `pdfjs.GlobalWorkerOptions.workerPort`.

#### Scenario: Worker construction is unavailable
- **WHEN** the runtime does not expose browser worker APIs
- **THEN** the reader still configures `pdfjs.GlobalWorkerOptions.workerSrc` as a fallback path.
