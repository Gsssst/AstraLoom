## 1. Scholarly Candidate Normalization

- [x] 1.1 Preserve normalized publication timestamps and provider identifiers in scholarly paper results.
- [x] 1.2 Replace digest arXiv-only retrieval with bounded multi-source retrieval, exact freshness filtering, and canonical deduplication.

## 2. Explainable Personalization

- [x] 2.1 Collect bounded preference signals from active research projects, saved or read papers, and recent digest feedback.
- [x] 2.2 Rank digest candidates with explainable scoring and persist source, score, reasons, and trusted ingestion metadata.

## 3. Feedback Loop UI and API

- [x] 3.1 Add an authenticated digest-paper feedback endpoint with ownership validation and allowed actions.
- [x] 3.2 Add interested, read-later, and not-interested actions to the digest inbox while preserving historical-card compatibility.

## 4. Verification

- [x] 4.1 Add regression tests for timestamp parsing, deduplication, ranking metadata, and feedback persistence.
- [x] 4.2 Run backend tests, frontend build/layout checks, strict OpenSpec validation, and local browser verification when available.
