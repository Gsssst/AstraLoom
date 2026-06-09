## Why

Some production browsers can fetch the bundled pdf.js worker asset with the correct MIME type but still fail pdf.js' fallback worker setup with `Failed to fetch dynamically imported module`. The reader should initialize pdf.js with an explicit module `Worker` port instead of relying on `workerSrc` fallback behavior.

## What Changes

- Initialize `pdfjs.GlobalWorkerOptions.workerPort` with a module worker created from the bundled pdf.js worker URL.
- Keep `workerSrc` as a fallback for environments where constructing a Worker is unavailable.
- Add contract coverage for explicit worker-port initialization.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `paper-reader-grounded-interaction`: The production PDF reader shall initialize the pdf.js worker through an explicit worker port when possible.

## Impact

- Affected file: `frontend/src/components/PDFViewer.tsx`.
- Affected tests: frontend PDF viewer contract test.
- No backend API or database changes.
