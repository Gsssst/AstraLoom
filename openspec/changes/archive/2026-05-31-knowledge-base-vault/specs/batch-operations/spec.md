## ADDED Requirements

### Requirement: 批量加标签
系统 SHALL 支持选中多篇论文批量添加标签。

#### Scenario: 批量标签
- **WHEN** 勾选 3 篇论文并点击"批量标签"
- **THEN** 弹出标签输入框，输入的标签同时应用到 3 篇论文

### Requirement: 批量导出
系统 SHALL 支持多选论文后一键导出 BibTeX。

#### Scenario: 批量导出
- **WHEN** 勾选论文并点击"导出 BibTeX"
- **THEN** 生成包含所有选中论文的 .bib 文件并下载
