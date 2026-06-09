## Why

The manuscript workbench currently shows `references.bib` and `figures/` as static project-structure labels, which makes them look like editable files while users cannot inspect or use them directly. Users need a lightweight Overleaf-style support-files surface that turns existing evidence cards and project metadata into usable BibTeX and figure insertion helpers without adding a real file-system layer yet.

## What Changes

- Add a BibTeX support panel for `references.bib` that is derived from the selected writing project's existing evidence cards.
- Allow users to view, copy, and regenerate the BibTeX content from evidence cards.
- Add a metadata-backed `figures/` panel that stores a figure manifest on the writing project and provides LaTeX insertion snippets.
- Make project-structure entries for `references.bib` and `figures/` clickable navigation targets instead of static labels.
- Keep the implementation scoped to current writing project metadata and evidence cards; no real file-system-backed asset storage is introduced.

## Capabilities

### New Capabilities

### Modified Capabilities
- `writing-manuscript-latex-workbench`: Add interactive support-file panels for BibTeX references and metadata-backed figures.

## Impact

- Frontend writing workbench: project file tree click behavior, BibTeX panel, figures panel, metadata editing.
- Backend writing project service/API: project support-file metadata persistence and BibTeX generation endpoint based on existing evidence.
- Tests: update writing workbench frontend contract and backend writing closed-loop coverage.
