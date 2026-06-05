# Proposal: Structured Paper Reading Assistant

## Why

The paper detail page can display metadata, PDF content, notes, and AI chat, but users still have to invent their own prompts for common reading tasks. This makes important workflows such as "explain the introduction", "extract method", "summarize experiments", and "find research gaps" feel unreliable and repetitive.

The backend paper chat already tries to load full text and can retrieve section-specific chunks when the question names a section. This change should expose that capability through a structured reading assistant instead of adding a new backend pipeline.

## What Changes

- Add a structured "AI 精读助手" panel to the paper detail content area.
- Provide reusable reading templates:
  - 全篇速读
  - 精读 Introduction
  - 拆解 Method
  - 分析 Experiments
  - 找 Research Gap
  - 生成组会提纲
- Let template clicks send a grounded paper-chat request directly, without requiring users to copy text into the input box.
- Improve empty chat quick prompts to reuse the same structured template set.
- Keep answers routed through the existing paper chat stream so thinking display, references, web search toggles, chat history, and failure recovery remain consistent.

## Out of Scope

- New database tables for generated summaries.
- Automatic background summarization for every paper.
- A separate LLM endpoint or new agent framework.
- Changing PDF parsing or paper retrieval algorithms.

## Risks

- Template prompts must be explicit enough to steer the model without encouraging hallucination.
- The panel should help reading without visually crowding the detail page.
- Triggering a template while an answer is streaming must be disabled to avoid overlapping turns.
