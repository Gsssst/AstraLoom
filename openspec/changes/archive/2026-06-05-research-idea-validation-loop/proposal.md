## Why

研究方向模块已经能生成 idea、给出 novelty/adversarial review、实验计划和反馈演化，但这些信号分散在多个区域，用户很难判断一个 idea 是否已经适合进入实验或写作。现在需要加入一个清晰的验证闭环，把“是否撞车、证据够不够、实验是否可做、能否进入写作”集中呈现。

## What Changes

- 为每个研究 idea 提供独立的验证结果，汇总 novelty/collision 风险、相关/冲突工作、可行性风险、实验最小清单和写作准备度。
- 新增后端验证接口，基于已有证据、review_json、experiment_plan 和论文集合上下文生成确定性诊断，不额外消耗大模型 token。
- 在研究项目页的 idea 卡片中加入“验证闭环”入口和结果面板，让用户能在推进前看到缺口。
- 当证据不足、实验计划不完整或 novelty 风险高时，明确提示不能直接进入写作，而不是让用户自行推断。

## Capabilities

### New Capabilities
- `research-idea-validation-loop`: Covers validation summaries for generated research ideas, including collision risk, evidence gaps, experiment checklists, feasibility risks, and writing readiness.

### Modified Capabilities

## Impact

- Backend research idea workbench service.
- Research API routes under `/api/research/*`.
- Research project frontend idea card and validation panel.
- Backend authorization tests and focused research workbench tests.
