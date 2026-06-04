## Why

当前论文管理方式是扁平列表，缺少结构化组织。参考 LobeChat 的 Knowledge Base 功能（支持文件夹、标签筛选、批量管理），我们的论文库需要升级为「知识库 Vault」：支持分类文件夹、批量操作、导出/导入。

## What Changes

- 论文库新增文件夹/收藏夹功能（可创建、嵌套、移动论文）
- 批量操作：多选后批量加标签、导出一组论文
- 知识库首页看板：显示各分类论文数量、最近添加
- 导入/导出：支持 BibTeX 导入、JSON 导出
- 前端论文库 UI 升级：左侧分类树 + 右侧论文列表

## Capabilities

### New Capabilities

- `paper-folders`: 论文文件夹管理与嵌套
- `batch-operations`: 批量操作（标签、导出、移动）
- `import-export`: BibTeX 导入 / JSON 导出

### Modified Capabilities

- `paper-models`: 新增 Folder 模型和 Paper-Folder 关联
- `paper-api`: 新增文件夹 CRUD API
