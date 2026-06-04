## ADDED Requirements

### Requirement: Cross-Encoder 重排序
系统 SHALL 使用 Cross-Encoder 模型对检索结果进行重排序。

#### Scenario: 重排序候选结果
- **WHEN** 检索返回 top-20 候选论文
- **THEN** Cross-Encoder 对每个 (query, paper) 对计算相关度分数
- **AND** 结果按新分数重新排序后返回 top-k

#### Scenario: 延迟控制
- **WHEN** 候选结果超过 20 条
- **THEN** 仅对前 20 条做交叉编码器重排序
- **AND** 总延迟增加不超过 300ms

### Requirement: RAG 检索升级
RAG 服务 SHALL 使用混合检索 + 重排序提升上下文质量。

#### Scenario: RAG 检索升级
- **WHEN** 对话中触发知识库检索
- **THEN** 使用混合检索（hybrid）模式替代纯向量检索
- **AND** 重排序后返回 top-5 论文作为上下文
