# paper-api Specification

## Purpose
TBD - created by archiving change paper-search-ingest. Update Purpose after archive.
## Requirements
### Requirement: 论文搜索 API
系统 SHALL 提供 REST API 供前端和内部服务搜索论文。

#### Scenario: 搜索已知论文
- **WHEN** 发送 `GET /api/papers/search?q=diffusion+models&source=arxiv&max_results=10`
- **THEN** 返回 JSON 数组，每项包含 paper_id, title, authors, year, abstract, arxiv_id, source
- **AND** 响应包含分页元数据（total, page, page_size）

#### Scenario: 空搜索结果
- **WHEN** 搜索查询无匹配结果
- **THEN** 返回空数组和 total=0

### Requirement: 论文入库 API
系统 SHALL 提供 REST API 触发论文检索和入库。

#### Scenario: 按 arXiv ID 入库
- **WHEN** 发送 `POST /api/papers/ingest` with `{"arxiv_ids": ["2301.12345", "2302.67890"]}`
- **THEN** 按 ID 查找论文元数据 → 去重 → 入库
- **AND** 返回入库结果（success_count, skipped_count, error_count）

#### Scenario: 按搜索查询入库
- **WHEN** 发送 `POST /api/papers/ingest` with `{"search_query": "large language model alignment", "max_results": 20}`
- **THEN** 搜索 arXiv → 去重 → 入库
- **AND** 自动提交 PDF 下载任务

### Requirement: 论文详情 API
系统 SHALL 提供论文详情查询接口。

#### Scenario: 查询论文详情
- **WHEN** 发送 `GET /api/papers/{paper_id}`
- **THEN** 返回论文完整信息：元数据 + 全文前 5000 字符 + 分类标签 + 入库时间

#### Scenario: 论文不存在
- **WHEN** 发送查询请求但 paper_id 不存在
- **THEN** 返回 404 错误

### Requirement: 分类管理 API
系统 SHALL 提供论文分类的 CRUD 接口。

#### Scenario: 获取分类树
- **WHEN** 发送 `GET /api/categories`
- **THEN** 返回多级分类树结构

#### Scenario: 为论文设置分类
- **WHEN** 发送 `PUT /api/papers/{paper_id}/categories` with `{"category_ids": [...]}`
- **THEN** 更新论文的分类关联

