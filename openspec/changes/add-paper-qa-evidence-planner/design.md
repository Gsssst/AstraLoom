## Context

Paper-detail Q&A now builds context by retrieving a small set of chunks from full text, structured PDF blocks, and ready visual evidence. This prevents unsupported hallucination, but it under-serves broad analytical questions. For example, "分析实验" should gather all experiment tables and visual table evidence, while the current flow can return only a few top-k snippets and then instruct the model to say "当前论文内容不足" too eagerly.

Similar open-source RAG systems separate query analysis from retrieval. LlamaIndex RouterQueryEngine uses a selector to route a query to one or more query engines; Haystack ConditionalRouter routes requests through different pipeline branches; LangChain's query-routing patterns separate query interpretation from context retrieval. We will implement the same idea locally with deterministic rules and existing evidence services rather than introducing a new framework.

## Goals / Non-Goals

**Goals:**

- Add an explicit paper Q&A evidence plan before retrieval.
- Route broad experiment/result/table questions to a complete bounded evidence pack.
- Route method/architecture questions to method text plus relevant visual/caption evidence.
- Keep ordinary specific questions on the current top-k retrieval path.
- Expose the selected plan in response metadata for tests and future UI diagnostics.
- Make insufficiency language precise: distinguish "no paper evidence", "missing exact table values", and "visual evidence unavailable".

**Non-Goals:**

- Do not add a new LLM call just to classify every question.
- Do not send whole PDFs or all page images to the model.
- Do not remove existing top-k retrieval for narrow questions.
- Do not guarantee every table cell is OCR-correct; evidence packs must preserve confidence and missing-data warnings.

## Decisions

1. **Use deterministic `QuestionEvidencePlan` first.**
   - Add a small dataclass or typed dict in the paper evidence service containing `intent`, `strategy`, `sections`, `include_all_tables`, `include_visual_tables`, `include_visual_evidence`, `budget`, and `warnings`.
   - Rationale: intent detection can use existing keyword/section detectors and is cheap, testable, and predictable.
   - Alternative considered: LLM-based planning on every request. Rejected for latency, cost, and instability.

2. **Add complete bounded pack builders alongside top-k retrieval.**
   - `experiment_complete` strategy gathers experiment/evaluation/result section chunks, all structured table blocks, all ready visual table blocks, table captions, and related chart/figure captions up to configured budgets.
   - `method_visual` strategy gathers method/approach section chunks plus architecture/figure/caption visual evidence.
   - `top_k` remains the default for narrow lookup.
   - Rationale: broad analytical questions need coverage before ranking; narrow questions still benefit from precision.

3. **Rank inside packs only after mandatory evidence is included.**
   - For experiment questions, all table-like evidence is mandatory within budget. Text chunks can then be ranked and truncated.
   - Rationale: tables are the primary source for experimental claims, and missing them creates poor answers even if text snippets score higher.

4. **Budget by evidence type, not only total top-k.**
   - Use separate caps for table blocks, visual table blocks, captions, section chunks, and total characters.
   - If truncation occurs, add a context warning such as "部分表格因预算被截断" instead of saying the whole paper is insufficient.

5. **Make insufficiency guardrails conditional.**
   - If no evidence exists, keep "当前论文内容不足".
   - If evidence exists but exact numeric table values are absent or visual OCR is missing, instruct the model to say that specific evidence is unavailable.
   - Rationale: this keeps anti-hallucination behavior without making the assistant sound like it cannot read the whole paper.

## Risks / Trade-offs

- [Risk] Complete experiment packs may be long. -> Enforce per-type and total character budgets and surface truncation warnings.
- [Risk] Deterministic intent detection may misclassify mixed questions. -> Allow multiple flags and prefer broader evidence packs when experiment/table/method terms are present.
- [Risk] Including all table captions without table cells can still be weak evidence. -> Preserve parser confidence and missing OCR/markdown warnings in context.
- [Risk] More evidence can reduce answer focus. -> Prompt the model with the selected plan and requested synthesis structure.
