## Why

科研工作流系统的核心是论文检索与知识积累。当前系统只有基础设施骨架，缺少实际的论文搜索和入库能力。用户需要能够从 arXiv 等学术源检索论文，系统自动提取元数据、去重后存入数据库，为后续的语义搜索、Idea 生成和写作辅助提供数据基础。

## What Changes

- 集成 arXiv API，支持按关键词、分类、时间范围搜索论文
- 集成 Semantic Scholar API 作为补充数据源（提供引用关系等增强元数据）
- 实现论文元数据提取：标题、作者、年份、摘要、DOI、arXiv ID、分类标签
- 实现自动去重逻辑（基于 arXiv ID / DOI / 标题相似度）
- 实现论文 PDF 下载和全文提取（通过已建立的 Celery 异步任务）
- 创建论文相关的数据库模型（papers 表、分类关联表）
- 创建 Alembic 迁移脚本
- 提供论文搜索 API（GET /api/papers/search）和论文详情 API
- 前端论文库页面：论文列表、分类筛选、搜索
- 支持 LLM 推荐论文（通过对话中用户的研究方向，推荐相关论文）

## Capabilities

### New Capabilities

- `paper-search`: 论文检索服务，支持 arXiv 和 Semantic Scholar API，关键词 + 分类 + 时间范围搜索
- `paper-ingestion`: 论文入库流水线，元数据提取 → 去重 → 存储 → PDF 下载 → 全文解析
- `paper-api`: 论文相关 REST API 端点（搜索、详情、分类、导入）
- `paper-models`: 论文数据库模型（papers, categories, paper_categories）

### Modified Capabilities

<!-- 首次建立论文模块，无已有规范需修改 -->

## Impact

- 新增后端依赖：`arxiv` (Python arXiv API 客户端), `feedparser`, `PyMuPDF` (已在 paper_tasks 中使用)
- 新增数据库表：`papers`, `categories`, `paper_categories`
- 新增 Alembic 迁移
- 前端 PaperPage 从占位页升级为完整论文库界面
- 后端新增 `backend/app/services/paper_search.py` 和 `backend/app/services/paper_ingestion.py`
