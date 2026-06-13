## 1. Visual Evidence Readiness

- [x] 1.1 Add effective-kind helpers so readiness/status counts use vision-corrected non-table types when present.
- [x] 1.2 Persist parser kind and vision-corrected kind metadata when OCR result type differs from parser kind.
- [x] 1.3 Keep actual table candidates strict: table-effective items still require markdown for OCR completeness.

## 2. Processing Alignment

- [x] 2.1 Ensure background pipeline and manual extraction use the same visual readiness criteria after OCR correction.
- [x] 2.2 Verify forced extraction clears stale asset-error payloads when rendering succeeds.

## 3. Verification

- [x] 3.1 Add backend regression tests for a parser table corrected to figure/text not counting as missing OCR.
- [x] 3.2 Add backend regression coverage for stale asset errors being replaced by a successful forced extraction/status.
- [x] 3.3 Run targeted backend tests and OpenSpec validation.
- [x] 3.4 Commit the completed change.
