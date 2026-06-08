## 1. Backend LaTeX Preview

- [x] 1.1 Add helpers to wrap a section LaTeX body in a minimal document and assemble project LaTeX for preview.
- [x] 1.2 Add project/section LaTeX preview-check endpoints that return compiler status, errors, warnings, and logs.
- [x] 1.3 Add backend tests for section preview wrapping, full-project preview, and compiler-unavailable diagnostics.

## 2. Manuscript Information Architecture

- [x] 2.1 Restructure paper writing mode so manuscript workbench is the default and survey creation is moved out of the manuscript panel.
- [x] 2.2 Split survey/literature-review actions into a separate workflow surface.
- [x] 2.3 De-emphasize template selection in manuscript creation while preserving export/submission profile controls.

## 3. Chapter LaTeX Workbench UI

- [x] 3.1 Update the section editor to label and preserve LaTeX source editing.
- [x] 3.2 Add section navigation/active-section focus so only the selected chapter is edited in the primary panel.
- [x] 3.3 Add section and manuscript preview/check actions with diagnostics display.

## 4. Section AI Assistant

- [x] 4.1 Add a section-scoped AI assistant panel with actions for draft, improve, evidence insertion, claim safety, polish, and LaTeX error repair.
- [x] 4.2 Pass current section title/source plus project context into AI action requests or prompt scaffolds.
- [x] 4.3 Keep AI assistance out of top-level paper tabs unless it is explicitly a section-context action.

## 5. Verification

- [x] 5.1 Add/update frontend contract tests for manuscript/survey separation, LaTeX section editing, preview diagnostics, and section AI assistant.
- [x] 5.2 Run focused backend tests, frontend contract tests, frontend build, and OpenSpec validation.
