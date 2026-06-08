## Overview

Keep the backend route protected. The frontend will fetch `pdf_preview_url` through the configured `api` client, which already attaches and refreshes bearer tokens, then display an object URL in the iframe.

## Decisions

- Add a reusable `AuthenticatedPdfPreview` component under `frontend/src/components/writing/`.
- Accept the API-relative preview URL returned by the backend.
- Request the PDF with `responseType: "blob"`.
- Revoke stale object URLs on cleanup to avoid browser memory leaks.
- Use the blob URL for both iframe preview and the open button.

## Risks

- If token refresh fails, preview loading will show an error while the compile diagnostics remain visible.
- Blob URLs are local to the current tab, so they are intentionally not shareable.
