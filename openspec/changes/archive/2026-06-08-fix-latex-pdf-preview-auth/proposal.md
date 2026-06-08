## Why

LaTeX PDF previews are served by an authenticated API route, but browser iframes do not attach the app's bearer token. The iframe therefore renders the 401 JSON response instead of the compiled PDF.

## What Changes

- Load LaTeX preview PDFs through the authenticated API client as `blob` responses.
- Render the fetched blob URL in the iframe and open button.
- Show a clear failure message when the preview PDF cannot be loaded.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `writing-manuscript-latex-workbench`: Generated PDF previews must render for authenticated users instead of exposing raw 401 API responses.

## Impact

- Frontend writing preview rendering.
- No backend API contract change.
