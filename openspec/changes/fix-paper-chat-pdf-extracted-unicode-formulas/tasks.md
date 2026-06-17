## 1. Diagnosis

- [x] 1.1 Inspect the target paper's extracted page text, structured blocks, detector output, and retrieved evidence chunks.

## 2. Formula Retrieval Fix

- [x] 2.1 Relax numbered formula label parsing for PDF-extracted labels adjacent to headings.
- [x] 2.2 Strengthen Unicode display formula detection and reject prose setup fragments.
- [x] 2.3 Add narrow neighbor-page exact lookup before page-local fallback.
- [x] 2.4 Preserve metadata for exact, fallback, and neighbor-page matches.

## 3. Verification

- [x] 3.1 Add regression tests for the ALVTS formula 2 extraction shape.
- [x] 3.2 Run focused backend tests and strict OpenSpec validation.
- [x] 3.3 Commit the completed fix.
