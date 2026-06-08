## 1. Backend LaTeX Fallback

- [x] 1.1 Add source-level LaTeX fallback diagnostics for missing `pdflatex`.
- [x] 1.2 Surface compiler availability metadata in preview responses.

## 2. Frontend Editor Stability

- [x] 2.1 Change `SectionEditor` to use local draft state and debounced save.
- [x] 2.2 Flush the latest draft before preview, citation, quality, status, and AI actions.
- [x] 2.3 Update LaTeX diagnostic UI text to distinguish missing compiler from source errors.

## 3. Tests

- [x] 3.1 Add backend tests for missing compiler fallback diagnostics.
- [x] 3.2 Update frontend contract tests for debounced editor saves and latest-draft actions.

## 4. Verification

- [x] 4.1 Run focused backend tests, frontend contract tests, frontend build, and OpenSpec validation.
- [ ] 4.2 Commit implementation, archive the OpenSpec change, validate specs, and commit the archive.
