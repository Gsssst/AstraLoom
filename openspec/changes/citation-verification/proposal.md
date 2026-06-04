## Why

参考 OpenScholar 的核心优势：AI 生成的回答中，引用真实存在的论文。当前我们的 RAG 回答会标注引用的论文，但缺乏验证机制——如果 AI 编造了论文标题，用户无从判断。需要实现引用验证：在 AI 回复后，自动核实引用的标题是否确实来自知识库。

## What Changes

- 新增引用验证服务：解析 AI 回复中的 [1][2] 引用标记，验证对应论文是否存在
- RAG 回答后自动标注验证结果（✅ 已验证 / ⚠️ 待核实）
- 前端展示验证状态

## Capabilities

### New Capabilities

- `citation-validator`: 引用验证服务
