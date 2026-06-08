## Overview

Treat template removal as a metadata update on the writing project. Removing the template clears `submission_profile` and restores `latex_compile` to a safe default that does not reference missing style files.

## Backend

- Add `WritingProjectService.remove_submission_profile(project_id, user_id)`.
- Remove `metadata_json["submission_profile"]`.
- Set `metadata_json["latex_compile"]` to:
  - `layout: "single_column"`;
  - `document_class: "article"`;
  - empty `document_options`;
  - empty `packages`.
- Add `DELETE /api/writing/projects/{project_id}/submission-template`.

## Frontend

- Add a visible "移除模板" action when a project has a bound template.
- Surface the single-column / double-column / template selector in the manuscript workbench header near the "整篇 LaTeX 检查" action.
- Keep the selector in sync with the project metadata and use the existing save endpoint before preview/export.

## Risks

- Removing a template intentionally loses venue/template metadata. The user can re-upload the official template later.
- Template mode may remain unavailable after removal until another template is bound.
