## ADDED Requirements

### Requirement: Backend Image Provides LaTeX Compiler
The manuscript workbench SHALL provide a backend container image that includes `pdflatex` for full LaTeX compile previews.

#### Scenario: Backend image is rebuilt
- **WHEN** the backend Docker image is built from the project Dockerfile
- **THEN** the resulting container includes a `pdflatex` executable
- **AND** section or manuscript LaTeX preview can perform compile checks instead of always using source-level fallback.
