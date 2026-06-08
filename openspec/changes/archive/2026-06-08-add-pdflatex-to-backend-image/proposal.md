## Why

LaTeX preview can only run full compile checks when `pdflatex` exists in the backend runtime. The Docker backend image currently lacks TeX packages, so containerized deployments always fall back to source-level diagnostics.

## What Changes

- Install a minimal `pdflatex`-capable TeX distribution in the backend image.
- Include commonly needed LaTeX recommended packages and fonts for paper previews.
- Document verification through `docker compose exec backend pdflatex --version`.

## Capabilities

### New Capabilities

### Modified Capabilities

- `writing-manuscript-latex-workbench`: Containerized backend runtimes should provide `pdflatex` for full LaTeX preview checks.

## Impact

- Backend Docker image size increases due to TeX packages.
- No application code or database changes.
