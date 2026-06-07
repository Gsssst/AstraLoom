## Context

The backend now stores a `generated_code_project` manifest with project name, summary, setup instructions, run commands, entrypoints, safety notes, and validated files. The existing frontend can trigger generation and download the ZIP, but the UI does not yet make the generated package feel like an inspectable project workspace.

GitHub and AI-code-generation tools commonly use a two-pane project browser: a compact file tree on the left and a read-only code/markdown preview on the right. This gives users immediate confidence that a generated output is a coherent project without requiring them to download the ZIP first.

## Goals / Non-Goals

**Goals:**
- Display generated project metadata and runnable guidance before the file list.
- Show generated files as a stable file tree grouped by folders.
- Let users select a file and preview its content in a read-only pane.
- Provide copy actions for file content and run commands.
- Keep ZIP download and regeneration actions visible.
- Preserve legacy generated-code fallback.

**Non-Goals:**
- Add in-browser code editing.
- Add Monaco/CodeMirror or syntax highlighting dependencies.
- Execute generated experiments from the browser.
- Change generated project manifest schema or backend generation behavior.

## Decisions

### 1. Build a local lightweight browser component

The UI will use existing React, Ant Design, and CSS to render folder/file rows and a `pre`-based preview. This avoids adding a large editor dependency for read-only inspection.

Alternative considered: introduce Monaco Editor. Rejected because the current requirement is preview-only and Monaco would add bundle size and integration complexity.

### 2. Prefer README and declared entrypoints for defaults

When a package is present, the default selected file will be `README.md` if available, then the first entrypoint path, then the first file. This matches user intent: understand setup first, then inspect runnable code.

Alternative considered: always select the first file by path. Rejected because generated projects are more useful when the starting context is visible first.

### 3. Keep project actions near the project header

Download ZIP, regenerate, and key run-command copy actions will be placed in the project package header instead of buried in file rows. File-specific copy remains in the preview toolbar.

Alternative considered: action buttons per file row. Rejected because repeated buttons make the file tree noisy and compete with file selection.

### 4. Use responsive stacking for narrow screens

Desktop uses two columns; narrow screens stack summary, file tree, and preview. Fixed min-widths and wrapping will prevent long file paths or commands from overflowing.

## Risks / Trade-offs

- [Risk] Large generated files can make the preview visually heavy. -> Mitigation: keep preview in a scrollable region with stable max height.
- [Risk] Long file paths or commands can overflow. -> Mitigation: use `overflow-wrap: anywhere`, constrained grid columns, and copy buttons.
- [Risk] Legacy Ideas without project manifests could look broken. -> Mitigation: preserve legacy code fallback and expose regeneration guidance.
