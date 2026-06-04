## Why

当前论文检索仅使用 dense vector (MiniLM 384d) 做余弦相似度搜索。参考 PaperQA2 和 OpenScholar 的实践，纯向量搜索在学术文献场景存在两个问题：(1) 专业术语精确匹配不足——"Transformer" 和 "attention mechanism" 在语义空间接近但不如关键词精确；(2) 缺乏结果重排序——top-k 结果按原始分数排序，相关度判断不够准确。

PaperQA2 使用 Hybrid (BM25+Vector)+RCS 重排序，比纯向量搜索召回率提升 30%+。OpenScholar 使用双编码器+交叉编码器两阶段检索，引用准确率达到人类水平。

## What Changes

- 新增 BM25 关键词检索引擎（Tantivy/SQLite FTS5）
- 实现混合检索：BM25 结果 + 向量结果 → 融合去重
- 实现交叉编码器重排序（使用 ms-marco-MiniLM-L-6-v2 模型）
- 更新论文搜索 API 支持 `hybrid` 检索模式
- 更新 RAG 服务使用混合检索提升上下文质量
- **BREAKING**: 无，纯增量功能

## Capabilities

### New Capabilities

- `hybrid-search`: BM25 关键词 + Dense 向量混合检索服务
- `cross-encoder-rerank`: 交叉编码器重排序服务（两阶段检索）

### Modified Capabilities

- `rag-service`: 更新 `search_similar` 为混合检索模式
- `paper-api`: 搜索 API 新增 `search_mode` 参数

## Impact

- 新增后端依赖：`rank-bm25` (BM25 实现), `sentence-transformers` (cross-encoder)
- 论文搜索结果质量显著提升
- RAG 回答的引用准确度提升
- 无前端破坏性变更
