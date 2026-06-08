## Overview

Keep the existing preview endpoints and response shape, but add optional PDF preview metadata when `pdflatex` successfully generates a PDF. The backend writes preview PDFs to a temporary preview directory and serves them through an authenticated static route by tokenized filename.

## Backend

- Extend `LatexProcessor.compile_check()` to:
  - run `pdflatex` as it already does;
  - detect `document.pdf` on success;
  - copy it to a preview directory under `/tmp/auto-research-latex-previews`;
  - return `pdf_preview_url`, `pdf_filename`, and `has_pdf_preview`.
- Use UUID filenames so preview URLs do not expose project or section names.
- Add a FastAPI route that returns preview PDFs by filename with `application/pdf`.
- Keep compiler-unavailable fallback and failure diagnostics unchanged.

## Frontend

- When a preview response includes `pdf_preview_url`, render it in an iframe below diagnostics.
- Use a stable bounded preview height so the section editor layout does not jump unexpectedly.
- Preserve the existing compile log collapse for warnings and failures.

## Risks

- Temporary preview files can accumulate. This is acceptable for local development but should be revisited if deployment becomes persistent or multi-user at scale.
- A PDF iframe may fail if the browser blocks inline PDF rendering. In that case the preview URL still opens/downloads the PDF.
