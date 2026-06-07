## Why

Generated research implementation output is now a structured project package, but the research Idea UI still needs a project-browser experience so users can inspect files, read setup guidance, and download the package without treating it like a single snippet.

## What Changes

- Add a file-tree browser for generated research code project files.
- Add a read-only file preview pane with file purpose, language, line count, copy action, and empty-state handling.
- Surface README/setup instructions, run commands, entrypoints, safety notes, and ZIP download in a compact project summary.
- Preserve legacy generated-code display for Ideas that do not yet have a structured project package.
- Add frontend contract tests for the project browser behavior.

## Capabilities

### New Capabilities

### Modified Capabilities

- `research-code-project-generation`: The generated project package SHALL be browsable as a project with file tree, metadata, command affordances, and downloads.

## Impact

- Research project frontend page and supporting styles.
- Frontend API/types for generated project package metadata if needed.
- Frontend contract tests for project browser rendering.
