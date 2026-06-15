## Why

项目空间已经能绑定论文、研究方向、写作草稿和 Issue，但概览仍偏“资源列表”，用户需要在多个标签页和模块之间来回判断下一步。参考 GPT Researcher 的 planner/research/report 分层、STORM 的多视角知识组织，以及 Open Notebook 的 notebook 化资料管理，项目空间应成为论文证据、Idea 推进和写作落地的统一入口。

## What Changes

- 在项目空间详情概览中加入“科研驾驶舱”，集中展示证据语料、Idea 推进、写作落地、开放问题四个工作流状态。
- 提供从驾驶舱直接绑定论文、进入研究方向、进入写作工作台、打开 Issue、调用空间助手诊断的动作。
- 复用现有 workspace summary、dashboard、next actions、issue summary 和资源绑定能力，不引入数据库迁移。
- 保持 owner/editor/viewer 的权限边界：编辑动作仅对可编辑成员开放，只读成员仍可查看和跳转。

## Capabilities

### New Capabilities

### Modified Capabilities
- `workspace-research-dashboard`: 项目空间仪表盘需要从静态指标升级为可执行科研驾驶舱，展示论文证据、研究方向、写作和 Issue 的闭环状态与下一步动作。
- `workspace-launchpad`: 项目空间启动台需要保留原快速入口，并补充面向科研闭环的驾驶舱入口与空间助手诊断动作。

## Impact

- 前端：`frontend/src/pages/WorkspaceDetailPage.tsx`、相关前端契约测试。
- OpenSpec：新增本 change 的 proposal/design/tasks 和相关规格 delta。
- 后端：第一版复用现有接口，不修改数据库和 API。
