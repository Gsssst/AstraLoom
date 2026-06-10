## Context

The production frontend serves `/assets/` with `Cache-Control: public, immutable` for one year. That is correct for most Vite hashed assets, but the pdf.js worker asset can keep the same content hash across changes to nginx MIME handling or frontend worker initialization. If a browser cached a bad worker response while `.mjs` was mis-served, it may continue failing dynamic import.

## Decisions

- Append a stable version query to the worker URL in `PDFViewer`.
- Add a more specific nginx location for `pdf.worker.min-*.mjs` before the generic `/assets/` location.
- Use `Cache-Control: public, max-age=300, must-revalidate` for the worker asset.

## Non-Goals

- Disabling immutable cache for all frontend assets.
- Changing the backend PDF proxy.
- Replacing pdf.js.

## Risks

- The worker asset may be revalidated more often than other hashed assets, but the file is only requested when opening PDFs and correctness matters more than long-lived caching.
