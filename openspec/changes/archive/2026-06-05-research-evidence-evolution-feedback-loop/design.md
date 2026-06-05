# Context

研究项目当前已有证据地图、单次 Proposal 演化和项目级实验记录。下一阶段需要把三者连成同一条可追溯工作流。

# Goals

- 外部论文一键进入本地论文库，并成为项目的持久证据。
- Proposal 可以连续演化，每一轮保留父版本、轮次和理由。
- 实验记录可以回流到 Proposal 演化提示中。
- 不新增数据库迁移，优先复用现有 JSON 字段和父子关系。

# Decisions

## Import external evidence from the latest run

前端只提交证据标识。后端从当前项目最近一次工作台运行的证据地图定位条目，避免信任前端提交的完整元数据。入库复用 `PaperIngestionService` 的去重逻辑，并将本地论文 ID 追加到项目 `paper_ids`。

## Persist lineage with existing parent relation

继续使用 `ResearchIdea.parent_idea_id`。子版本在 `evolution_json` 中记录 `round`、关注点、演化理由和可选实验反馈。谱系接口根据父子关系返回当前 Proposal 的祖先与后代版本。

## Bind experiments to proposals

实验继续存放在项目 `metadata_json.experiments`，但每条记录增加稳定 `experiment_id` 和可选 `idea_id`。反馈演化接口只接受属于当前项目且绑定当前 Proposal 的实验。

# Risks

- 外部证据缺少作者信息。证据地图入库保留当前已知元数据，后续 PDF 解析和元数据更新仍可补全。
- JSON 存储不适合复杂分析查询。当前阶段保持迁移成本较低，后续实验规模扩大时再拆独立表。

