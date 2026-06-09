## Why

The production paper PDF reader can fetch the PDF successfully but fail before rendering because pdf.js cannot dynamically import the generated `.mjs` worker asset. The frontend container must serve module worker assets with a JavaScript MIME type.

## What Changes

- Configure the frontend Nginx image to serve `.mjs` files as JavaScript modules.
- Keep the existing bundled pdf.js worker path and PDF proxy unchanged.
- Add contract coverage for the frontend Nginx MIME mapping.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `paper-reader-grounded-interaction`: The production PDF reader shall be able to load its pdf.js worker asset from the frontend server.

## Impact

- Affected file: `frontend/nginx-frontend.conf`.
- Affected tests: frontend PDF viewer contract test.
- No backend API or database changes.
