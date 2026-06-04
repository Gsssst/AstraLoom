## Why

研究方向工作台已经能生成证据驱动的 Proposal，写作助手也能从研究方向创建综述草稿，但两者目前仍是分开的。用户需要把一个看中的 Proposal 手动复制到写作页，证据论文也不会自动带入，研究闭环在写作这一步断开。

## What Changes

- 在研究 Proposal 上新增“一键生成写作草稿”入口。
- 后端基于 Proposal 的标题、假设、技术方案、证据论文和实验计划创建综述/Related Work 写作项目。
- 写作项目 metadata 记录来源研究项目、来源 Idea 和证据论文，后续 BibTeX 导出可复用这些论文。
- 写作页支持通过 URL 参数打开刚创建的写作项目。
- 生成的草稿明确区分 Proposal 背景、证据表、方法定位、实验计划和引用清单。

## Capabilities

### New Capabilities
- `research-to-writing-evidence-bridge`: Covers converting evidence-grounded research ideas into writing projects and preserving evidence/citation links across the transition.

### Modified Capabilities

## Impact

- Backend research API and writing project service.
- Frontend research project page and writing page routing behavior.
- Backend tests for idea-to-writing draft conversion.
