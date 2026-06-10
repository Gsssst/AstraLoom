## Context

The previous fixes confirmed the backend PDF endpoint can return a valid PDF and that the worker module is served with a JavaScript MIME type. The remaining production-only symptom is an unresolved loading state: no visible pdf.js error, no page count, and no rendered page.

Local development differs from production because Vite serves modules dynamically without long-lived asset caching, while production uses nginx static assets and a reverse-proxied PDF endpoint. pdf.js can issue range/streaming requests and may remain pending if the proxy path behaves differently from local development.

## Decisions

- Pass a pdf.js document descriptor with `disableRange`, `disableStream`, and `disableAutoFetch`.
- Preserve the same-origin resolved PDF URL behavior.
- Add a loading watchdog so the UI surfaces a diagnostic instead of spinning indefinitely.
- Keep the user escape hatch simple: direct link to the same PDF endpoint.

## Non-Goals

- Replacing react-pdf/pdf.js.
- Changing the backend PDF cache.
- Adding a server-side renderer.

## Risks

- Full-file loading may be less efficient for very large PDFs, but it is more predictable for lab-scale paper reading behind a reverse proxy.
