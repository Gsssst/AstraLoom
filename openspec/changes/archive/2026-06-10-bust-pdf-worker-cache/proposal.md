## Why

Production PDF preview still fails with `Failed to fetch dynamically imported module` for the bundled `pdf.worker.min-*.mjs` asset even after the MIME type fix. The PDF proxy itself returns valid cached PDFs quickly. The likely remaining root cause is a stale browser or proxy cache for the worker asset, because `/assets/` is served with long-lived immutable caching and the worker content hash may not change after server config fixes.

## What Changes

- Add a stable application version query to the pdf.js worker URL to bust stale worker-module caches.
- Serve `pdf.worker.min-*.mjs` with a shorter revalidation cache policy instead of one-year immutable caching.
- Keep regular hashed assets immutable.

## Capabilities

### Modified Capabilities
- `paper-reader-grounded-interaction`: The production PDF reader avoids stale cached pdf.js worker module failures.

## Impact

- Affected files: `frontend/src/components/PDFViewer.tsx`, `frontend/nginx-frontend.conf`.
- Affected tests: frontend PDF viewer contract test.
- No backend API or database changes.
