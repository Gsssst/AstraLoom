## Context

The writing workbench already has a manuscript-first layout, evidence cards, LaTeX preview, export package generation, and an Overleaf-style project file tree. However, `references.bib` and `figures/` are currently informational rows. This creates a mismatch: the UI suggests files exist, but users cannot inspect or use them.

Similar writing tools such as OpenPrism and Rxiv-Maker treat references and figures as first-class paper-project resources. For AstraLoom, the pragmatic version is to expose those resources through existing evidence cards and project metadata rather than adding a real file-system layer.

## Goals / Non-Goals

**Goals:**
- Make `references.bib` open a panel with evidence-derived BibTeX that users can view, copy, and regenerate.
- Make `figures/` open a panel backed by `metadata_json.support_files.figures`.
- Provide LaTeX figure snippets that users can copy or insert into the active section.
- Keep the project file tree as the navigation entry point for support files.

**Non-Goals:**
- No physical `references.bib` or `figures/` directory is created on disk.
- No binary image upload, storage, or serving is introduced in this change.
- No overhaul of the LaTeX compiler/export pipeline beyond using the existing BibTeX export and metadata.

## Decisions

1. Store figure manifest data under `metadata_json.support_files.figures`.
   - Rationale: the user explicitly asked to avoid a complex file system. Metadata storage is enough for labels, paths, captions, and snippets.
   - Alternative considered: create upload-backed asset models. Rejected as heavier than this change and likely to add feature bloat.

2. Generate BibTeX from the existing evidence cards / export service.
   - Rationale: evidence cards already represent the papers backing a manuscript. Reusing this source avoids a second reference list that can drift.
   - Alternative considered: let users hand-edit a standalone BibTeX document. Rejected for now because it creates synchronization questions with evidence and citations.

3. Use file-tree rows as scroll/navigation controls.
   - Rationale: users already see `references.bib` and `figures/` in the file structure. Turning those rows into buttons makes the mental model clear without adding another navigation system.

## Risks / Trade-offs

- Metadata figure entries can reference files that do not actually exist yet -> Label the panel as a manifest/snippet helper and avoid implying upload-backed storage.
- Evidence-derived BibTeX may be incomplete when evidence cards are external-only -> Show readiness counts and empty/incomplete states.
- Copy-only snippets are less powerful than a full asset manager -> Keep insertion into the active section available so the workflow is still useful.
