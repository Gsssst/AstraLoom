## Why

当前论文页 AI 问答（`build_paper_context`）将论文全文（最多 8000 字符）直接塞入 System Prompt 作为上下文。这导致：
1. **Token 浪费**：大部分全文内容与用户问题无关，白白占用上下文窗口
2. **思考消耗大**：DeepSeek V4 Pro 需要对整个全文进行推理，消耗大量 reasoning tokens
3. **回答质量差**：模型面对 8000 字符的全文难以定位关键信息

应改为：将论文全文按段落切片 → 检索与问题最相关的片段 → 仅将相关片段注入上下文（参考 RAG 架构）。

## What Changes

- **论文全文切片服务**：将论文 `full_text` 按段落/句子切分为 500-1000 字符的 chunks，使用关键词+向量混合检索
- **`build_paper_context` 重构**：从"全部塞入"改为"检索 top-3 最相关片段"，metadata（标题、作者、摘要）始终保留
- **Token 节省**：单次请求节省约 5000-7000 tokens（从 8000 字符全文 → 3 × 800 字符相关片段）
- **向后兼容**：无全文的论文继续使用摘要作为上下文

## Capabilities

### New Capabilities

- `paper-chunk-retrieval`: 论文章节级检索 — 将论文全文切片，根据用户问题检索最相关片段

### Modified Capabilities

- `writing-pipeline`: build_paper_context 重构为混合检索模式（metadata + 相关 chunks）

## Impact

- **后端**: `app/services/memory_service.py` `build_paper_context` 重构；新增 `app/services/paper_chunk_service.py`
- **无数据库变更**：chunks 在内存中处理，不持久化
- **无前端变更**
