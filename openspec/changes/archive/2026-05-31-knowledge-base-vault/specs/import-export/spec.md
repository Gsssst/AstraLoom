## ADDED Requirements

### Requirement: BibTeX 导入
系统 SHALL 支持上传 .bib 文件导入论文元数据。

#### Scenario: 导入 BibTeX
- **WHEN** 上传包含 10 条论文的 .bib 文件
- **THEN** 系统解析并导入所有论文（自动去重）
- **AND** 返回导入结果（成功/跳过/失败数量）

### Requirement: JSON 导出
系统 SHALL 支持将全部或筛选后的论文导出为 JSON。

#### Scenario: JSON 导出
- **WHEN** 调用 POST /api/papers/export with format=json
- **THEN** 返回包含所有论文元数据的 JSON 文件
