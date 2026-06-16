## 1. Formula Evidence Routing

- [x] 1.1 Add formula/equation intent detection to `PaperChunkService`.
- [x] 1.2 Extend evidence plan metadata with formula evidence budget and warnings.
- [x] 1.3 Implement a formula evidence lane that ranks structured formula blocks and merges them with primary paper evidence.
- [x] 1.4 Preserve numbered-section, table, visual, and experiment retrieval behavior.

## 2. Answer Context Tone

- [x] 2.1 Update paper Q&A prompt guidance so missing formula details are scoped to the specific missing evidence.
- [x] 2.2 Reduce over-severe wording that makes local evidence gaps sound like whole-method unreliability.

## 3. Verification

- [x] 3.1 Add regression tests for formula query retrieval.
- [x] 3.2 Add regression tests for numbered-section answers receiving supplemental formula evidence.
- [x] 3.3 Add regression tests for calibrated insufficiency guidance.
- [x] 3.4 Run focused backend tests and strict OpenSpec validation.
- [x] 3.5 Commit the completed optimization.
