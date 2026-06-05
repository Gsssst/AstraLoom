# paper-ingestion Specification

## Purpose
TBD - created by archiving change paper-search-ingest. Update Purpose after archive.
## Requirements
### Requirement: 论文元数据提取
系统 SHALL 从 arXiv 和 Semantic Scholar API 响应中提取结构化元数据。

#### Scenario: 提取 arXiv 论文元数据
- **WHEN** 收到 arXiv API 的论文条目
- **THEN** 提取：标题、作者列表（含 affiliations）、摘要、arXiv ID、DOI（如有）、发表年份、分类标签、PDF URL
- **AND** 元数据以 Paper ORM 模型格式存储

#### Scenario: 提取 Semantic Scholar 论文元数据
- **WHEN** 收到 Semantic Scholar API 的论文条目
- **THEN** 提取：标题、作者、摘要、DOI、引用次数、参考文献列表
- **AND** 标注来源为 "semantic_scholar"

### Requirement: 论文自动去重
系统 SHALL 在新论文入库前进行三级去重检查。

#### Scenario: arXiv ID 精确去重
- **WHEN** 待入库论文的 arXiv ID 已存在于数据库
- **THEN** 跳过该论文，标记为"已存在"

#### Scenario: DOI 精确去重
- **WHEN** 待入库论文的 DOI 已存在于数据库且非空
- **THEN** 跳过该论文，标记为"已存在"

#### Scenario: 标题相似度去重
- **WHEN** 待入库论文的 arXiv ID 和 DOI 均不匹配任何已有论文
- **THEN** 计算其标题与数据库中所有论文标题的编辑距离相似度
- **AND** 若最高相似度 > 0.85，跳过该论文，标记为"疑似重复"
- **AND** 若最高相似度 ≤ 0.85，将论文入库

### Requirement: 异步 PDF 处理
系统 SHALL 在论文入库后，自动提交异步任务下载 PDF 并提取全文。

#### Scenario: 自动触发 PDF 下载
- **WHEN** 新论文入库且 `auto_download=true`
- **THEN** 自动向 Celery 提交 PDF 下载任务
- **AND** 下载完成后提交 PDF 解析任务
- **AND** 解析结果（全文文本）写入 Paper.full_text 字段

#### Scenario: PDF 下载失败处理
- **WHEN** PDF 下载失败（网络错误、文件不存在等）
- **THEN** Paper.pdf_path 保持为 NULL
- **AND** 任务状态记录失败原因

