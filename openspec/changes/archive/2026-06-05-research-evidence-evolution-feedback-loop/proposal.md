## Why

研究工作台已经能生成外部证据和 Proposal，但证据、版本演化与实验记录仍是彼此分离的页面信息。用户需要把外部发现沉淀为论文库资产，并通过连续实验反馈逐轮收敛研究方案。

## What Changes

- 在证据地图中为外部论文增加一键入库，并自动关联当前研究项目。
- 为 Proposal 提供可查看的多轮父子谱系和轮次信息。
- 让实验记录绑定具体 Proposal，保留结构化结果和备注。
- 支持根据某次实验反馈生成可追溯的新 Proposal 版本。
- 在研究项目页增加实验反馈面板、入库状态和谱系查看入口。

## Capabilities

### New Capabilities

- `research-feedback-loop`: 外部证据沉淀、多轮 Proposal 演化和实验反馈驱动演化闭环。

### Modified Capabilities

- None.

## Impact

- Backend API: `app/api/research.py`
- Backend services: `app/services/research_idea_workbench.py`, `app/services/digest_service.py`
- Frontend: `frontend/src/pages/ResearchProjectPage.tsx`
- Tests: research workbench and authorization regression tests

