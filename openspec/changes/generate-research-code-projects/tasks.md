## 1. Backend Project Package Model

- [x] 1.1 Add a nullable `generated_code_project` JSON column and ORM/API response fields.
- [x] 1.2 Define code project response schemas for package metadata, commands, entrypoints, safety notes, and files.
- [x] 1.3 Add package normalization helpers for safe paths, bounded file counts, representative legacy code, and fallback projects.

## 2. Backend Generation And Download

- [x] 2.1 Replace single-string code generation with structured package generation and JSON parsing/fallback.
- [x] 2.2 Persist the generated package while keeping `generated_code` compatible for legacy callers.
- [x] 2.3 Add an authorized zip download endpoint for generated project packages.

## 3. Frontend Project Package Experience

- [x] 3.1 Extend Research Idea types and state updates to include generated project packages.
- [x] 3.2 Replace the single code block with project metadata, setup/run commands, file list, and selected file preview.
- [x] 3.3 Add download action and legacy-code fallback/regeneration UI.

## 4. Verification

- [x] 4.1 Add backend tests for package normalization, fallback generation, persistence shape, and zip download safety.
- [x] 4.2 Add frontend contract tests for project package rendering, download action, and legacy fallback.
- [x] 4.3 Run strict OpenSpec validation plus focused backend/frontend tests and frontend build checks.
