## Context

pdf.js supports two worker paths:

- `workerSrc`: pdf.js creates a Worker and runs a test handshake before resolving it.
- `workerPort`: the application supplies a Worker object and pdf.js trusts it.

The app added `workerPort` to avoid a fake-worker dynamic import error. After `.mjs` MIME handling was fixed, `workerSrc` is the safer path because pdf.js can validate the worker itself. A manually supplied singleton `workerPort` also risks reuse and lifecycle mismatches across React mounts.

## Decision

Use only `pdfjs.GlobalWorkerOptions.workerSrc = pdfWorkerUrl`.

## Non-Goals

- Removing the native preview fallback.
- Changing PDF proxy responses.
- Changing react-pdf dependencies.

## Risks

- If the deployed worker asset is still blocked, pdf.js will surface an explicit worker/fake-worker error instead of hanging behind an externally supplied worker port.
