## Context

The backend service runs in `python:3.12-slim` through `backend/Dockerfile`. Full LaTeX checking shells out to `pdflatex`; when the binary is missing, the app now degrades to source-level diagnostics. Installing TeX packages in the backend image enables real compile checks for Docker Compose deployments.

## Goals / Non-Goals

**Goals:**
- Make `pdflatex` available in the backend container.
- Keep the package set reasonably small while supporting common article templates.
- Preserve the existing Python build flow.

**Non-Goals:**
- Do not install a full TeX Live distribution unless needed.
- Do not add runtime package installation at container startup.
- Do not change the LaTeX preview API.

## Decisions

1. **Install Debian TeX packages at image build time.**
   - Rationale: deterministic and works for backend/celery images built from the same Dockerfile.
   - Alternative: ask users to install TeX on the host. That does not help a containerized backend.

2. **Use `texlive-latex-base`, `texlive-latex-recommended`, and `texlive-fonts-recommended`.**
   - Rationale: this provides `pdflatex` and covers common academic article macros/fonts without pulling the entire TeX Live suite.
   - Trade-off: some venue-specific templates may still require extra packages later.

## Verification

- Rebuild the backend image.
- Run `docker compose exec backend pdflatex --version`.
- Run a LaTeX preview from the writing workbench.
