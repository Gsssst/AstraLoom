## Why

Production PDF reading can remain in a loading state after the worker is available because pdf.js may use range or streaming requests through the nginx-to-backend proxy. The local Vite development server does not exercise the same static asset caching and proxy behavior, so the issue can appear only after deployment.

## What Changes

- Load proxied PDFs with a conservative full-file pdf.js descriptor.
- Disable range, stream, and auto-fetch behavior for the in-app reader.
- Add a bounded loading timeout with a visible diagnostic and a direct PDF fallback link.

## Capabilities

### Modified Capabilities
- `paper-reader-grounded-interaction`: PDF loading must avoid infinite spinner states in production proxy deployments.

## Impact

- Affected file: `frontend/src/components/PDFViewer.tsx`.
- Affected tests: frontend PDF viewer contract test.
- No backend API or database changes.
