## ADDED Requirements

### Requirement: 论文文件夹
系统 SHALL 支持创建多级文件夹组织论文。

#### Scenario: 创建文件夹
- **WHEN** 用户创建文件夹 "NLP Papers"
- **THEN** 文件夹出现在左侧分类树中
- **AND** 可将论文拖入该文件夹

#### Scenario: 嵌套文件夹
- **WHEN** 创建子文件夹 "NLP Papers > Alignment"
- **THEN** 父文件夹可展开显示子文件夹

### Requirement: 文件夹 CRUD API
系统 SHALL 提供文件夹的创建、读取、更新、删除接口。

#### Scenario: 获取文件夹树
- **WHEN** 调用 GET /api/folders
- **THEN** 返回完整文件夹树结构（含论文数量）
