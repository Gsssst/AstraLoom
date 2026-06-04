# publication-export-package

## Why

The writing module already has drafts, evidence cards, citation checks, and basic single-format exports, but users still need to manually collect Markdown, BibTeX, Word files, and quality warnings before using a draft for group meetings, submissions, or collaborator handoff. This makes the final research-output step feel fragmented.

P7 should turn a writing project into a coherent exportable publication package.

## What Changes

- Add an export readiness summary for writing projects.
- Add a publication package API that returns Markdown, BibTeX, LaTeX, reference list, warnings, and downloadable DOCX metadata in one response.
- Add safer filename handling and clearer export status labels.
- Add a frontend export panel in the writing project workspace.
- Keep existing single-format export endpoints working.

## Non-Goals

- Full PDF compilation through TeX engines.
- Journal-specific style files or camera-ready submission templates.
- External Pandoc integration.
- Automatic citation correction beyond existing citation checks.

## Reference Patterns

- Manubot-style pipelines separate manuscript Markdown from citation metadata.
- Pandoc/Zettlr-style workflows treat Markdown as editable source and BibTeX as the citation source.
- Lightweight research workbenches commonly expose export readiness warnings before producing final files.

## Success Criteria

- Users can inspect whether a writing project is ready for export.
- Users can copy or download Markdown, BibTeX, LaTeX, and reference-list outputs from the writing project page.
- Users can download Word from the same export panel.
- Export output includes evidence/citation coverage warnings instead of silently producing weak drafts.
- Backend and frontend builds/tests pass.
