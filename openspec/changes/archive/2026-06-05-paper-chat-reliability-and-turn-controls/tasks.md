## 1. Paper Answer Reliability

- [x] 1.1 Add a paper-specific visible-answer recovery stream and recovery status event
- [x] 1.2 Keep the existing warning as the final fallback when both paper streams fail

## 2. Per-Turn Thinking Display

- [x] 2.1 Attach reasoning content and streaming state to individual main-chat assistant turns
- [x] 2.2 Attach and persist reasoning content per assistant turn in paper-detail Q&A

## 3. Paper History Controls

- [x] 3.1 Add an authenticated endpoint that clears only saved paper-chat history
- [x] 3.2 Add a confirmed clear-history action to the paper-detail AI Q&A panel

## 4. Verification

- [x] 4.1 Add backend regression tests for paper-answer recovery behavior
- [x] 4.2 Run backend tests, frontend packaging verification, and strict OpenSpec validation
