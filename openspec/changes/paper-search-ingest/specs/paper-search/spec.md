## ADDED Requirements

### Requirement: arXiv API 搜索
系统 SHALL 通过 arXiv API 搜索论文，支持关键词、分类、时间范围过滤。

#### Scenario: 关键词搜索
- **WHEN** 调用搜索服务并传入查询关键词 "transformer attention mechanism"
- **THEN** 返回匹配的 arXiv 论文列表，每篇包含标题、作者、摘要、arXiv ID、年份、URL
- **AND** 结果按相关度排序

#### Scenario: 分类过滤
- **WHEN** 搜索时指定 `category=cs.AI`（人工智能分类）
- **THEN** 仅返回该分类下的论文

#### Scenario: 时间范围过滤
- **WHEN** 搜索时指定 `year_from=2024` 和 `year_to=2026`
- **THEN** 仅返回该时间范围内发表的论文

#### Scenario: API 速率限制处理
- **WHEN** arXiv API 返回 503（过载）或连接超时
- **THEN** 系统自动使用指数退避重试（最多 3 次）
- **AND** 3 次重试后仍然失败则返回错误信息

### Requirement: Semantic Scholar API 搜索
系统 SHALL 集成 Semantic Scholar API 作为补充论文源，提供引用关系等增强元数据。

#### Scenario: 补充搜索
- **WHEN** 搜索 `source=semantic_scholar`
- **THEN** 返回 Semantic Scholar 的论文列表，包含 citationCount 和 referenceCount

#### Scenario: API 频率控制
- **WHEN** 5 分钟内 Semantic Scholar API 请求超过 100 次
- **THEN** 系统自动等待直至配额恢复

### Requirement: LLM 论文推荐
系统 SHALL 支持通过 LLM 分析用户研究方向，自动推荐相关论文。

#### Scenario: 对话式推荐
- **WHEN** 用户在对话中描述研究方向（如"我对多模态大语言模型的对齐问题感兴趣"）
- **THEN** 系统从对话中提取关键研究方向
- **AND** 自动搜索 arXiv 中该方向的最新论文
- **AND** 返回推荐论文列表供用户确认入库
