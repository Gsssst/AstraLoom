## Context

当前仅使用 MiniLM 384d 向量做余弦相似度检索。PaperQA2 和 OpenScholar 的实践证明：学术文献检索需要混合 BM25（精确术语匹配）+ Dense（语义匹配），并用交叉编码器重排序。

## Goals / Non-Goals

**Goals:**
- 实现 BM25 关键词检索（使用 `rank-bm25` Python 库）
- 实现混合融合策略（BM25 + Vector 分数归一化后加权合并）
- 实现 Cross-Encoder 重排序（使用 `ms-marco-MiniLM-L-6-v2`）
- 更新 RAG 和搜索 API 支持混合模式

**Non-Goals:**
- 不替换现有向量数据库（pgvector 保留）
- 不做 Elasticsearch/Solr 等重量级方案
- 不改变前端 UI

## Decisions

### 1. BM25 实现：使用 `rank-bm25` 轻量库

**选择**：Python 内存级 BM25，对论文标题+摘要建立索引

**替代**：Tantivy（Rust 高性能，但引入编译依赖）→ 被排除以简化部署

### 2. 融合策略：RRF (Reciprocal Rank Fusion)

**公式**: `score = α * normalize(dense_score) + (1-α) * normalize(bm25_score)`

α = 0.7（向量权重更高），归一化到 [0,1]

### 3. 重排序：Cross-Encoder

使用 sentence-transformers 的 `cross-encoder/ms-marco-MiniLM-L-6-v2`（约 80MB）
- 输入：(query, document) 对
- 输出：相关度分数 [0, 1]
- 仅对 top-20 候选做重排，控制延迟

## Risks / Trade-offs

- BM25 索引在内存中重建 → 论文入库后需刷新索引，增加内存占用
- Cross-Encoder 推理增加 ~200ms 延迟 → 仅对 top-20 做，总体可控
