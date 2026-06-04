## Why

写作模块已经具备引用推荐、综述生成、引用验证和项目导出的基础能力，但这些能力目前偏分散，用户从“研究方向”走到“可编辑综述草稿”和“可信引用”仍需要手动拼接。现在需要把写作助手升级为一个闭环：能从研究方向创建草稿、生成 Related Work 对比表、解释推荐引用的用途，并在导出前帮助检查引用真实性和句子匹配度。

## What Changes

- 从研究方向一键创建综述写作项目，自动填充综述草稿、Related Work 对比表、研究空白和参考文献章节。
- 生成 Related Work 对比表，按论文、年份、方法/贡献、证据角色、可对比点组织。
- 引用推荐结果新增证据角色：支持证据、反例/局限、基线方法、背景资料，并展示匹配强度与原因。
- 新增句子级引用匹配检查，判断引用论文是否真实存在，以及是否支持当前句子。
- 写作项目导出补齐 BibTeX，并与既有 Markdown、Word 导出形成统一入口。

## Capabilities

### New Capabilities
- `writing-assistant-closed-loop`: Covers topic-to-review draft creation, role-aware citation recommendations, sentence-citation checks, Related Work comparison tables, and BibTeX/Markdown/Word export for writing projects.

### Modified Capabilities

## Impact

- Backend writing services and writing project services.
- Writing API routes under `/api/writing/*`.
- Writing page UI, especially citation recommendation, Related Work, and project management tabs.
- Backend tests for writing service behavior and API contracts.
