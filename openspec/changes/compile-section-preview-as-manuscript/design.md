## Overview

Keep the current section preview endpoint and UI flow, but change the generated TeX source from a single-section wrapper to the full manuscript export. The active section draft supplied by the editor replaces the matching project section in the assembled manuscript before compilation.

## Backend

- Load the writing project with its ordered sections through the existing service path.
- Build a preview section list from `project["sections"]`.
- Replace the matching section when `section_id` equals a section id.
- Preserve the section's existing metadata such as id, level, and order while replacing `title` and `content` with the current editor draft.
- If no section id match exists, fall back to title match, then append the draft section so users still get a useful preview.
- Compile the merged list with `latex_processor.render_to_tex(project_title, sections, template="article")`.
- Return existing diagnostic fields plus:
  - `scope: "section"` for endpoint compatibility;
  - `pdf_scope: "manuscript"`;
  - `preview_mode: "manuscript_with_active_section"`.

## Frontend

- Continue storing the response in the current section preview state.
- Label the compiled PDF as an assembled manuscript preview when `pdf_scope` is `manuscript`.
- Keep existing authenticated PDF blob loading and diagnostic panels.

## Risks

- Errors from other manuscript sections may appear when the user clicked a section preview button. This is intentional because the PDF now represents the assembled paper; the UI label must make that clear.
- If the active draft is not found in the project sections, appending it may produce duplicate-looking content. This is preferable to silently omitting the user's current draft.
