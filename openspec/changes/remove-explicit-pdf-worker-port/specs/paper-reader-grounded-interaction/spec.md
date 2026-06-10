## ADDED Requirements

### Requirement: PDF reader uses pdf.js standard worker initialization
The paper PDF reader SHALL configure the bundled pdf.js worker source and SHALL let pdf.js create and test its worker rather than injecting an externally supplied worker port.

#### Scenario: Reader module configures pdf.js
- **WHEN** the paper PDF reader module loads
- **THEN** it assigns the bundled worker module URL to `pdfjs.GlobalWorkerOptions.workerSrc`
- **AND** it does not assign `pdfjs.GlobalWorkerOptions.workerPort`.

#### Scenario: Worker initialization fails
- **WHEN** pdf.js cannot initialize the configured worker source
- **THEN** pdf.js reports the worker failure through its standard loading error path
- **AND** the reader can fall back to native PDF preview.
