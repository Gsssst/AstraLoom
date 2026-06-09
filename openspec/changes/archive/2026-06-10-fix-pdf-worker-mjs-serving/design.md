## Context

Vite emits the pdf.js worker as a hashed `.mjs` asset under `/assets/`. In production, pdf.js dynamically imports that module. If Nginx serves `.mjs` as a generic MIME type, browsers can reject the module load, producing `Setting up fake worker failed` and `Failed to fetch dynamically imported module`.

## Goals / Non-Goals

**Goals:**
- Ensure the production frontend container serves `.mjs` assets as JavaScript.
- Preserve the existing bundling approach so worker assets remain cacheable and versioned.

**Non-Goals:**
- Changing the backend PDF proxy.
- Switching to CDN-hosted workers.
- Replacing `react-pdf`.

## Decisions

- Add a `types` mapping in `frontend/nginx-frontend.conf` for `application/javascript js mjs`.
- Keep immutable caching for `/assets/`; hashed worker assets are safe to cache.

## Risks / Trade-offs

- Some older Nginx images may already include `.mjs`; the explicit mapping is still harmless and makes behavior deterministic.
- Browser cache can keep the old failed asset response -> operators may need to hard refresh after redeploy.
