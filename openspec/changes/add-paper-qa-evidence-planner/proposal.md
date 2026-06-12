## Why

Paper-detail Q&A currently treats most questions as a top-k retrieval problem. That is too narrow for user requests such as "analyze the experiments", "summarize all ablations", or "explain the method from the figures", where the answer needs a complete evidence pack across sections, tables, captions, and ready visual/table evidence rather than only the highest-scoring snippets.

## What Changes

- Add a lightweight question evidence planning step before paper Q&A context construction.
- Classify paper questions into evidence intents such as overview, section focus, method, experiment, table/result analysis, visual/figure, and narrow lookup.
- Route experiment/result questions to a complete bounded experiment evidence pack containing experiment-section text, all structured tables, all ready visual tables, relevant captions, and visual evidence metadata within token budget.
- Route method/architecture questions to method-section text plus ready visual evidence/captions before generic top-k snippets.
- Keep top-k retrieval for narrow lookup questions.
- Soften "当前论文内容不足" guardrails so the assistant distinguishes between no paper evidence, missing table values, missing visual OCR, and partial support.
- Expose evidence plan metadata in paper Q&A responses so the frontend and tests can verify which strategy was used.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `paper-qa-evidence-grounding`: Paper Q&A must plan evidence strategy before retrieval and use complete bounded evidence packs for broad method/experiment questions.
- `paper-multimodal-visual-evidence`: Experiment/table and method/architecture questions must include all ready visual table or relevant visual evidence within budget instead of relying on top-k selection alone.

## Impact

- Backend services: paper Q&A context construction, paper chunk/evidence retrieval, prompt guardrails, response evidence metadata.
- Tests: paper reader grounded interaction tests for experiment-pack routing, table completeness, and narrowed insufficiency wording.
- Frontend: optional display of evidence plan metadata in existing evidence meta contract; no new user-facing workflow required.
- Dependencies: no new runtime framework dependency. Similar GitHub patterns were reviewed in LlamaIndex RouterQueryEngine, Haystack ConditionalRouter, and LangChain query/context routing, but implementation remains local and deterministic.
