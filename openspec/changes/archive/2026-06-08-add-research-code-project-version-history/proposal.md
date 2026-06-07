## Why

Research code projects are iterative assets. Re-generating a package currently overwrites the previous project, which makes it hard to compare how experiments evolve after discussion, review, or feedback.

## What Changes

- Persist a version snapshot each time a structured research code project is generated.
- Add backend APIs to list project versions, retrieve a version manifest, and compare two versions at file level.
- Add file-level diff metadata for added, removed, modified, and unchanged files.
- Extend the research Idea UI with version history, version switching, and version comparison.
- Preserve the current `generated_code_project` field as the latest package for backward compatibility.

## Capabilities

### New Capabilities

### Modified Capabilities

- `research-code-project-generation`: Generated experiment project packages SHALL keep version history and support file-level version comparison.

## Impact

- Backend data model and Alembic migration for code project versions.
- Research code generation service and research API routes.
- Research project frontend code browser.
- Backend/frontend regression tests and OpenSpec archive.
