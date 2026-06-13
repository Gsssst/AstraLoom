## 1. Visual Table OCR

- [x] 1.1 Enable default OCR for all weak visual table items while preserving an optional deployment cap.
- [x] 1.2 Detect weak visual table markdown and prioritize those items for system-model OCR.
- [x] 1.3 Preserve OCR markdown, OCR text, confidence, uncertainty notes, and model metadata on visual evidence items.

## 2. Paper Q&A Evidence Planning

- [x] 2.1 Classify broad Chinese experiment-analysis questions as `experiment_complete`.
- [x] 2.2 Prefer OCR-enhanced visual table markdown over low-fidelity parser table markdown when assembling experiment evidence.

## 3. Verification

- [x] 3.1 Add unit tests for weak visual table OCR eligibility and result persistence.
- [x] 3.2 Add evidence-planner regression tests for Chinese experiment-analysis prompts.
- [x] 3.3 Re-run targeted backend tests, OpenSpec validation, and diff checks.
- [x] 3.4 Commit the completed change.
