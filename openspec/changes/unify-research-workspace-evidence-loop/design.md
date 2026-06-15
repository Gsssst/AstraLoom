## Overview

第一版以“前端聚合现有上下文”为主，不新建后端数据模型。项目空间详情接口已经返回 `summary.linked_resources`、`dashboard`、`next_actions`、`issue_summary`，页面也已经加载 Issue 列表和空间 AI 助手状态。本变更在概览页新增驾驶舱组件，把这些数据按科研流程重新组织。

## UI Model

驾驶舱分为四个轨道：

1. 证据语料：绑定论文数量、示例论文、绑定论文/查看论文操作。
2. Idea 推进：绑定研究方向数量、示例方向、进入研究方向操作。
3. 写作落地：绑定写作草稿数量、示例草稿、进入写作操作。
4. 开放问题：Open Issue 数量、高优先级提示、进入 Issue 操作。

每个轨道展示：

- 状态标签：已就绪 / 待补齐 / 有待处理问题。
- 资源数量和最多 3 个可点击资源。
- 面向当前角色的主动作。

## Assistant Actions

驾驶舱底部提供空间助手快捷诊断：

- “诊断证据缺口”
- “规划下一步 Idea”
- “检查写作落地风险”

点击后复用现有 `sendAssistantMessage(contentOverride)`，不会新增 AI 接口。

## Permissions

- owner/editor：可看到绑定论文入口和资源绑定动作。
- viewer：只能查看资源和跳转模块，不显示绑定类操作。

## Risks

- 如果空间资源过少，驾驶舱可能显得空。通过状态标签和助手诊断引导补齐。
- 如果资源标题过长，需使用 `Text ellipsis` 保证布局稳定。
