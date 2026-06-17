## 1. Diagnosis

- [x] 1.1 Confirm multi-formula questions only retrieve the first formula number.
- [x] 1.2 Confirm paper chat input is top-level page state and can trigger full page re-renders.

## 2. Backend Multi-Formula Retrieval

- [x] 2.1 Add multi-number formula detection.
- [x] 2.2 Retrieve evidence for each requested formula number and preserve metadata.
- [x] 2.3 Scale formula evidence budget for multi-number questions.
- [x] 2.4 Add regression tests for formulas 8, 9, and 10 in one question.

## 3. Frontend Composer Responsiveness

- [x] 3.1 Extract a memoized paper chat composer with local draft state.
- [x] 3.2 Update submit/retry/clear flows to use composer ref methods.
- [x] 3.3 Preserve send disabled state for empty text, quote, attachments, and extraction status.

## 4. Verification

- [x] 4.1 Run focused backend tests.
- [x] 4.2 Run frontend type/build verification if available.
- [x] 4.3 Run strict OpenSpec validation.
- [x] 4.4 Commit the completed fix.
