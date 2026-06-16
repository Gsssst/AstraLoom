## Context

Mature chat tools expose a stop control for active streams. The main chat page already implements this with an `AbortController`, a cancellation flag, and finalization of the streaming message. Paper-detail chat currently lacks the same control even though it uses streamed SSE.

For evidence routing, PaperQA-style systems separate retrieval from generation: they retrieve candidate evidence, structure it by intent, then generate grounded answers from those candidates. The current paper-detail Q&A already has this architecture, but several user intents still fall through to generic top-k retrieval.

## Goals / Non-Goals

**Goals:**
- Let users stop an active paper-detail answer without leaving stale loading UI.
- Route explicit formula-number questions to matching formula blocks.
- Route dataset questions to experiment/table/caption evidence.
- Route novelty questions to method plus experiment/ablation evidence.

**Non-Goals:**
- Do not add persistent backend cancellation jobs; client abort is enough for the streamed fetch.
- Do not rewrite PDF parsing.
- Do not implement external web lookup for these current-paper questions.

## Decisions

- Reuse the main chat AbortController pattern in `PaperDetailPage`.
  - Rationale: The product already has a working local pattern for stopping streamed chat.

- Add deterministic intent detectors to `PaperChunkService`.
  - Rationale: Questions like "公式 1" and "用了哪些数据集" have clear lexical signals and should not rely on generic chunk similarity.

- Treat explicit formula-number targets as a formula evidence lane filter before generic formula scoring.
  - Rationale: The user means the paper's numbered/ordered formula, not the first prose expression that looks like math.

- Use existing experiment-complete evidence pack for novelty questions, with method evidence merged in.
  - Rationale: Novelty evaluation needs both method claims and experiment/ablation support.

## Risks / Trade-offs

- Client abort may not instantly terminate upstream model work -> The UI stops immediately and the browser closes the request; server/provider cancellation depth depends on the runtime stream implementation.
- Formula extraction may lack numbered formula blocks -> The route falls back to formula lane plus text evidence and still surfaces the evidence limitation in prompt warnings.
- Dataset names may only appear in tables -> The dataset route prioritizes tables and captions before generic text.
