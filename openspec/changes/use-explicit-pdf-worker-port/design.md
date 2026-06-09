## Context

The previous fixes made PDF proxy responses valid and ensured `.mjs` assets are served as JavaScript. The remaining production error comes from pdf.js failing to set up its fake worker after dynamic import. pdf.js supports an explicit `GlobalWorkerOptions.workerPort` that receives a real module `Worker`.

## Goals / Non-Goals

**Goals:**
- Prefer a real module worker for pdf.js in browser environments.
- Preserve compatibility with test/SSR-like environments where `Worker` is unavailable.
- Avoid CDN-hosted worker dependencies.

**Non-Goals:**
- Changing backend PDF serving.
- Replacing react-pdf/pdf.js.
- Adding another server-side PDF rendering dependency.

## Decisions

- Compute the bundled worker URL with Vite's `new URL(..., import.meta.url)` asset handling.
- If `window.Worker` exists and no worker port is already configured, set `pdfjs.GlobalWorkerOptions.workerPort = new Worker(workerUrl, { type: "module" })`.
- Keep `workerSrc = workerUrl` as a fallback.

## Risks / Trade-offs

- Browsers that block workers entirely will still fail -> the visible diagnostic from the previous change will surface that browser/runtime error.
- Worker ports should be singleton-like -> initialize at module load and only if `workerPort` is not already set.
