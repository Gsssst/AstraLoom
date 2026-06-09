## Why

Server deployments can return valid PDF bytes from the backend while the paper reader still shows only the generic pdf.js "Failed to load PDF file" message. The frontend needs a production-safe PDF loading path and actionable error feedback so operators can distinguish API, worker, and asset issues.

## What Changes

- Load paper PDFs through an explicit `react-pdf` file descriptor instead of a bare relative string.
- Add PDF load error state that surfaces a concise diagnostic message in the reader.
- Keep the existing PDF proxy API and server PDF cache unchanged.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `paper-reader-grounded-interaction`: The PDF reader shall handle production PDF loading failures with stable loading inputs and clear diagnostics.

## Impact

- Affected file: `frontend/src/components/PDFViewer.tsx`.
- Affected tests: frontend PDF viewer contract test.
- No backend API or database changes.
