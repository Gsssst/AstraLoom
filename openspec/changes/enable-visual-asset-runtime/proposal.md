## Why

The visual evidence code path is already wired into paper Q&A, but the backend runtime does not install PyMuPDF/`fitz`, so real PDF visual asset extraction fails before it can render pages or crops. This makes visual evidence maintenance appear present while the feature is not operational.

## What Changes

- Declare and install the PyMuPDF runtime dependency used by PDF page rendering and crop generation.
- Expose visual extraction readiness through existing parser/runtime health checks so missing `fitz` is visible before users run maintenance.
- Add focused tests proving visual asset extraction can render a real PDF page into a persisted image asset.
- Keep the implementation dependency-light and do not introduce ColPali/Byaldi or a GPU visual index in this change.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `paper-multimodal-visual-evidence`: Visual asset extraction must be operational in the backend runtime, with explicit readiness diagnostics when the PDF rendering dependency is unavailable.

## Impact

- Backend dependency set: adds PyMuPDF.
- Backend visual extraction: real PDF rendering and crop generation can run in the app container.
- Backend tests: adds runtime/extraction coverage for visual assets.
- Deployment: backend and worker images must be rebuilt or dependencies installed so `import fitz` succeeds.
