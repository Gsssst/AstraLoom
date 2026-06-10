## Why

Production diagnostics prove the PDF proxy returns valid cached PDFs quickly and supports Range requests. The remaining silent loading stall points to the pdf.js worker/rendering path. The current reader injects `GlobalWorkerOptions.workerPort` manually, which bypasses pdf.js' built-in worker initialization and test handshake. If that externally supplied worker fails to communicate, pdf.js can wait without surfacing the previous fake-worker error.

## What Changes

- Stop injecting an explicit `workerPort`.
- Keep `workerSrc` pointed at the bundled worker module so pdf.js can create and test its own worker.
- Keep the native fallback as a user-facing safety net if pdf.js still fails.

## Capabilities

### Modified Capabilities
- `paper-reader-grounded-interaction`: The PDF reader relies on pdf.js standard worker initialization instead of an externally supplied singleton worker port.

## Impact

- Affected file: `frontend/src/components/PDFViewer.tsx`.
- Affected tests: frontend PDF viewer contract test.
- No backend API or database changes.
