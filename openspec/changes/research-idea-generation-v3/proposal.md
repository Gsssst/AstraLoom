## Why

当前研究方向工作台已经从证据出发生成 Proposal，但候选生成仍偏单轮：模型一次性给出候选，随后去重和评分。参考 AI-Scientist、SciPIP、PaperQA 和 STORM 后，下一步应把 Idea 生成升级为更可检查的探索过程：多分支搜索、检索式新颖性校验、反驳式评审。

## What Changes

- 候选生成后新增轻量分支搜索树：对高潜力候选做多轮变异，记录 parent、round、operator。
- 新增 Novelty Check：将候选与本地/外部证据标题和摘要做相似度检查，标记 `likely_novel`、`incremental`、`too_similar`。
- 新增 Adversarial Review：从 baseline、可证伪性、证据覆盖、实验成本等角度提出反驳意见和风险扣分。
- 最终 Proposal 的 `review_json` 保存 novelty check、反驳评审和搜索树 lineage。
- 研究方向页面展示新颖性状态和反驳意见摘要。

## Capabilities

### New Capabilities
- `research-idea-generation-v3`: Covers search-tree based candidate refinement, novelty checking, adversarial review, and UI visibility for these signals.

### Modified Capabilities

## Impact

- Backend research idea workbench generation pipeline.
- Research project frontend Proposal display.
- Regression tests for tree expansion, novelty check, adversarial review, and persisted review metadata.
