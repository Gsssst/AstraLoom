# Design

## Backend

Extend `WritingProjectService` with:

- `build_export_readiness(project_id, user_id)`
  - Counts sections, empty sections, total words.
  - Uses existing evidence cards for local/external/BibTeX coverage.
  - Uses existing section citation checker for citation warnings.
  - Produces a status: `ready`, `needs_attention`, or `incomplete`.

- `build_reference_list(project_id, user_id, style)`
  - Derives papers from existing project metadata and References section parsing.
  - Generates a readable numbered reference list.

- `build_publication_package(project_id, user_id)`
  - Returns Markdown, LaTeX, BibTeX, reference list, readiness summary, and file names.
  - Uses existing single-format exporters where possible.

Add API endpoints:

- `GET /api/writing/projects/{project_id}/export/readiness`
- `GET /api/writing/projects/{project_id}/export/package`
- `GET /api/writing/projects/{project_id}/export?format=references`

Keep existing `markdown`, `latex`, `docx`, `bibtex` behavior unchanged.

## Frontend

Add a publication export panel to the writing project tab:

- Shows readiness status, warnings, and coverage numbers.
- Offers buttons for copying Markdown/BibTeX/LaTeX/reference list.
- Keeps direct Word download.

## Testing

Add backend unit/regression tests around:

- Reference extraction from project metadata and References text.
- Readiness warnings for empty sections and weak evidence coverage.
- Package shape and route auth.

## Risks

- Citation readiness can be conservative because it relies on current evidence-card data.
- DOCX remains a generated stream, not embedded directly in JSON package.
- LaTeX export is template-light and not a full publisher template.
