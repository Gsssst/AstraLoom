## Context

The deployed PDF proxy returns valid PDFs quickly, including Range responses. When the in-app reader still times out, the likely failure layer is pdf.js worker/rendering behavior in the deployed browser environment or cached frontend assets.

## Decisions

- Keep pdf.js as the primary renderer because it enables text selection callbacks with page numbers.
- Switch to native preview on pdf.js load errors and loading timeouts.
- Render native preview with an iframe using the same resolved PDF URL.
- Show a concise notice explaining that native preview disables in-app page-aware selection and provide a retry button.

## Non-Goals

- Replacing pdf.js permanently.
- Adding a server-side PDF renderer.
- Changing PDF proxy behavior.

## Risks

- Browser-native PDF preview selection will not provide the same page-aware quote workflow.
- Some browsers may download PDFs instead of rendering them inline, but the endpoint already serves `Content-Disposition: inline`.
