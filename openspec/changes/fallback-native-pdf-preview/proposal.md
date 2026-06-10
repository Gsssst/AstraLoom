## Why

Diagnostics show production PDF proxy responses are healthy: cached PDFs return quickly, include a valid `%PDF-` signature, and support Range requests. Remaining preview failures are therefore browser-side pdf.js/worker/rendering failures. The reader should not block users from viewing papers when pdf.js stalls.

## What Changes

- Add a native browser PDF preview fallback for pdf.js failures and timeouts.
- Allow users to switch back from native preview to pdf.js when desired.
- Keep the existing pdf.js reader as the default so text-selection chat workflows remain available when it works.

## Capabilities

### Modified Capabilities
- `paper-reader-grounded-interaction`: The PDF reader falls back to browser-native PDF preview when pdf.js cannot render a valid proxied PDF.

## Impact

- Affected files: `frontend/src/components/PDFViewer.tsx`, `frontend/src/styles/responsive.css`.
- Affected tests: frontend PDF viewer contract test.
- No backend API or database changes.
