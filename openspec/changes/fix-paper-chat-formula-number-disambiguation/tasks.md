## 1. Request Context

- [x] 1.1 Extend paper chat request models with optional reading context/current page.
- [x] 1.2 Track current PDF page in the frontend PDF viewer and include it in ask payloads.

## 2. Formula Retrieval

- [x] 2.1 Add preferred-page support to numbered formula text extraction.
- [x] 2.2 Ensure page-local formula `(2)` beats earlier global `(2)` matches while preserving fallback.

## 3. Verification

- [x] 3.1 Add backend regression tests for duplicate formula numbers across pages.
- [x] 3.2 Run focused backend tests, frontend contract/type checks where available, and strict OpenSpec validation.
- [x] 3.3 Commit the completed fix.
