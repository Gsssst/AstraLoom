## ADDED Requirements

### Requirement: Paper 模型
系统 SHALL 定义 Paper ORM 模型用于存储论文数据，继承自 BaseModel。

#### Scenario: 创建论文记录
- **WHEN** 新论文入库
- **THEN** Paper 表新增一条记录，包含 id (UUID), title, authors (JSON), year, abstract, doi, arxiv_id, source, source_url, pdf_path, full_text, citation_count, metadata_json, created_at, updated_at

#### Scenario: arXiv ID 唯一索引
- **WHEN** 尝试插入已存在的 arXiv ID
- **THEN** 数据库抛出唯一约束异常

### Requirement: Category 模型
系统 SHALL 定义 Category ORM 模型支持多级分类树。

#### Scenario: 创建分类
- **WHEN** 创建 "cs.AI" 分类，parent_id 指向 "cs" 分类
- **THEN** Category 表新增记录，parent_id 引用父分类

#### Scenario: 获取分类下的论文
- **WHEN** 查询某分类下的论文
- **THEN** 返回该分类及其所有子分类下的论文（递归查询）

### Requirement: PaperCategory 关联模型
系统 SHALL 定义 PaperCategory 多对多关联模型连接论文和分类。

#### Scenario: 论文关联多个分类
- **WHEN** 一篇论文同时标记为 "cs.AI" 和 "cs.CL"
- **THEN** paper_categories 表新增两条记录
- **AND** 通过 Paper.categories 可访问所有关联分类

### Requirement: Alembic 迁移
系统 SHALL 为新模型创建数据库迁移脚本。

#### Scenario: 执行迁移
- **WHEN** 运行 `alembic upgrade head`
- **THEN** papers, categories, paper_categories 三张表被创建
- **AND** 索引被正确创建（arxiv_id unique index, doi index, title gin index for full-text search）
