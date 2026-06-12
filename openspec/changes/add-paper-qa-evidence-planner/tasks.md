## 1. Evidence Planning

- [x] 1.1 Add a deterministic paper question evidence planner with intents, strategies, requested sections, visual/table flags, and budget metadata.
- [x] 1.2 Expose evidence plan metadata through paper Q&A response evidence meta for streamed and non-streamed answers.

## 2. Complete Evidence Packs

- [x] 2.1 Add an experiment-complete evidence strategy that includes experiment-section text, all structured tables, all ready visual tables, table captions, and related chart/figure captions within budget.
- [x] 2.2 Add a method/visual strategy that prioritizes method-section text and ready architecture/figure/caption visual evidence before generic top-k snippets.
- [x] 2.3 Keep narrow lookup questions on the existing top-k retrieval path.

## 3. Prompt Guardrails

- [x] 3.1 Update paper Q&A context prompts to describe the selected evidence strategy and avoid overusing "当前论文内容不足" when partial evidence exists.
- [x] 3.2 Add specific warnings for missing table cell values, missing visual OCR, and budget truncation.

## 4. Tests And Verification

- [x] 4.1 Add backend tests proving experiment-analysis questions include all available table and visual table evidence instead of only top-k evidence.
- [x] 4.2 Add backend tests for evidence plan metadata and narrowed insufficiency wording.
- [x] 4.3 Run targeted backend tests and OpenSpec validation.
