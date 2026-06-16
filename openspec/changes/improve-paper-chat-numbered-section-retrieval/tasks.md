## 1. Numbered Section Evidence Routing

- [x] 1.1 Add numbered section request detection to `PaperChunkService` and expose it in the evidence plan metadata.
- [x] 1.2 Implement deterministic numbered heading range extraction from parsed paper text.
- [x] 1.3 Route exact numbered-section matches before generic semantic/top-k evidence retrieval.
- [x] 1.4 Add a precise missing-numbered-section warning when no exact heading is found.

## 2. Answer Context

- [x] 2.1 Ensure paper Q&A prompt guidance tells the model to mention the missing numbered section specifically, not just "current paper content insufficient".
- [x] 2.2 Preserve existing method/table/visual/experiment fallback behavior.

## 3. Verification

- [x] 3.1 Add regression tests for section-number detection, exact extraction, and missing-section fallback warnings.
- [x] 3.2 Run focused backend tests and strict OpenSpec validation.
- [x] 3.3 Commit the completed optimization.
