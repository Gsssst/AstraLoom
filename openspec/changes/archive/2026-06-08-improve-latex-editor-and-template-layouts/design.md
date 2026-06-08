## Overview

Implement a focused first version without replacing the editor dependency stack. Keep Ant Design TextArea and add command suggestion behavior around it. For templates, introduce a compile layout stored in project metadata and have the backend renderer translate that into `\documentclass` options and package lines.

## Frontend: LaTeX Command Suggestions

- Detect a LaTeX command token immediately before the cursor using `\\[A-Za-z]*`.
- Show a compact suggestion menu when the user types a backslash command prefix.
- Include common paper-writing snippets:
  - citations: `\cite{}`, `\citep{}`, `\citet{}`;
  - references: `\label{}`, `\ref{}`, `\eqref{}`;
  - structure: `\section{}`, `\subsection{}`, `\paragraph{}`;
  - environments: `equation`, `align`, `figure`, `table`, `itemize`, `enumerate`.
- Insert the selected snippet and place the cursor inside the most useful editable position.
- Support click selection plus keyboard `ArrowUp`, `ArrowDown`, `Enter`, and `Tab`.

## Backend: Template/Layout Rendering

- Extend `LatexProcessor.render_to_tex()` with a `render_options` dictionary.
- Supported options:
  - `layout`: `single_column`, `double_column`, or `template`;
  - `document_class`;
  - `document_options`;
  - `packages`.
- For `double_column`, render `\documentclass[twocolumn]{article}`.
- For `template`, use inspected `document_class` and package metadata when present, with fallback to article.
- Keep preview PDF generation and diagnostics unchanged.

## Project Metadata

- Store compile settings in `metadata_json["latex_compile"]`.
- Update profile binding so detected document class/packages seed compile settings when a user binds a template.
- Add a lightweight endpoint to update compile settings without replacing unrelated metadata.

## Risks

- TextArea-based command suggestions are not a full language-aware editor. This is acceptable for the first version and leaves room for a later CodeMirror migration.
- Template-informed rendering will not fully reproduce official templates until template files are persisted and included in the compile working directory.
