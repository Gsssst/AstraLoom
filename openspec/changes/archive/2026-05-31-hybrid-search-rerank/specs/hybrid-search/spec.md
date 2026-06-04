## ADDED Requirements

### Requirement: BM25 关键词检索
系统 SHALL 提供 BM25 关键词检索引擎，对论文标题和摘要建立索引，支持精确术语匹配。

#### Scenario: 关键词搜索
- **WHEN** 调用 BM25 搜索服务传入 "transformer attention BLEU"
- **THEN** 返回与关键词最匹配的论文列表，按 BM25 分数降序排列

#### Scenario: 索引更新
- **WHEN** 新论文入库后
- **THEN** BM25 索引自动重建，包含新论文

### Requirement: 混合检索融合
系统 SHALL 使用 RRF 算法融合 BM25 和 Dense 向量搜索结果。

#### Scenario: 混合搜索
- **WHEN** 调用搜索 API 并设置 `search_mode=hybrid`
- **THEN** 返回融合后的结果，包含 BM25 和语义双路召回的论文
- **AND** 结果去重并按融合分数排序

### Requirement: 搜索 API 拓展
搜索 API SHALL 支持 `search_mode` 参数。

#### Scenario: 指定检索模式
- **WHEN** `search_mode=hybrid` 时使用混合检索
- **WHEN** `search_mode=dense` 时仅使用向量检索（默认）
- **WHEN** `search_mode=bm25` 时仅使用关键词检索
