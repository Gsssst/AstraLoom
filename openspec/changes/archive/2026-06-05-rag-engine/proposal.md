## Why

当前系统已能检索和存储论文，但搜索仅支持关键词匹配。需要引入向量语义搜索和 RAG（检索增强生成），让用户能用自然语言描述想找的内容，并在与大模型对话时自动注入相关论文作为上下文。

## What Changes

- 为 Paper 表添加 embedding 列 (VECTOR(1536))
- 实现向量嵌入生成服务（调 DeepSeek Embedding API）
- 实现 pgvector 语义搜索
- 实现 RAG 服务：对话时自动检索相关论文并注入上下文
- 提供语义搜索 API 和论文引用的对话 API
- 前端聊天页面集成论文引用展示

## Capabilities

### New Capabilities

- `vector-embedding`: 向量嵌入生成与存储
- `semantic-search`: pgvector 语义相似度搜索
- `rag-service`: RAG 检索增强生成服务
- `rag-chat`: 带论文引用的对话接口
