## 1. Backend Data Model

- [x] 1.1 Add a `ResearchCodeProjectVersion` model and relationship to Research Ideas.
- [x] 1.2 Add an Alembic migration for the version table and indexes.

## 2. Backend Service And API

- [x] 2.1 Persist a normalized version snapshot whenever code generation succeeds.
- [x] 2.2 Add service helpers to list versions, load a version, and compare two manifests by file path.
- [x] 2.3 Add owner-scoped API routes for version list, version detail, and version compare.

## 3. Frontend Version Browser

- [x] 3.1 Add frontend types and API calls for code project versions and comparisons.
- [x] 3.2 Extend the project browser with version selector, history state, and older-version preview.
- [x] 3.3 Add comparison controls, diff summary, file rows, and compact diff preview.

## 4. Verification

- [x] 4.1 Add backend tests for version persistence and comparison behavior.
- [x] 4.2 Add frontend contract tests for version selector, diff summary, and no-history fallback.
- [x] 4.3 Run OpenSpec validation, backend tests, frontend tests, build, and local smoke checks.
