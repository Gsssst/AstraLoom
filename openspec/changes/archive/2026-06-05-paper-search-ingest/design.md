## Context

当前系统有 FastAPI 后端、PostgreSQL+pgvector 数据库和 Celery 异步任务队列，但缺少实际的论文检索和入库功能。本变更需要建立完整的论文数据管道：API 检索 → 元数据提取 → 去重 → 入库 → PDF 下载 → 全文解析。

## Goals / Non-Goals

**Goals:**
- 实现 arXiv API 搜索（search_query, id_list, 分类筛选, 时间范围）
- 实现 Semantic Scholar API 搜索（作为补充源，提供引用关系）
- 论文自动去重（基于 arXiv ID, DOI, 标题编辑距离）
- 论文元数据存储到 PostgreSQL
- 异步 PDF 下载和全文解析（复用已有 Celery 任务）
- 前端论文库页面：搜索框、列表、分类筛选

**Non-Goals:**
- 不做向量嵌入（留给后续 RAG 引擎 change）
- 不做论文总结（LLMService.summarize_paper 已在 project-scaffold 中就绪，但本 change 不做界面集成）
- 不做引用关系图谱

## Decisions

### 1. arXiv API 接入方式：使用 `arxiv` Python 库

**选择**：使用 `arxiv` 官方 Python 库封装 arXiv API 调用，返回结构化数据。

**原因**：
- `arxiv` 库已处理了 API 的 XML 解析和分页
- 支持 search, lookup by ID 两种模式
- 原生支持异步

**替代方案**：直接 HTTP 请求 arXiv API → 需要自行解析 Atom XML，增加维护成本

### 2. 去重策略：三级检查

1. **arXiv ID**：精确匹配（最可靠）
2. **DOI**：精确匹配
3. **标题相似度**：使用 `difflib.SequenceMatcher` 计算编辑距离相似度，阈值 > 0.85 视为重复

去重顺序：先查 arXiv ID → 再查 DOI → 最后模糊匹配标题。任一步命中即视为重复，跳过。

### 3. 数据库模型设计

```python
class Paper(BaseModel):
    title: str (indexed)
    authors: JSON (作者列表，含 affiliations)
    year: int (indexed)
    abstract: text
    doi: str (unique, nullable)
    arxiv_id: str (unique, nullable, indexed)
    source: str (arxiv / semantic_scholar / manual / llm_recommend)
    source_url: str
    pdf_path: str (nullable, PDF 文件本地路径)
    full_text: text (nullable, 解析后的全文)
    citation_count: int (default 0)
    metadata_json: JSON (存储源数据原始 JSON 备用)

class Category(BaseModel):
    name: str (unique)
    parent_id: UUID (nullable, 自引用支持多级分类)

class PaperCategory(BaseModel):
    paper_id: UUID (FK → papers)
    category_id: UUID (FK → categories)
```

### 4. 搜索 API 设计

```
GET /api/papers/search
  ?q=transformer+attention          # 关键词
  &source=arxiv                      # arxiv | semantic_scholar | all
  &category=cs.AI                    # arXiv 分类
  &year_from=2024                    # 时间范围
  &year_to=2026
  &max_results=20                    # 每页条数
  &page=1                            # 分页
  &sort=relevance                    # relevance | date | citations

POST /api/papers/ingest
  Body: { "arxiv_ids": [...], "search_query": "...", "auto_download": true }
  触发检索 + 入库 + 异步 PDF 下载

GET /api/papers/{paper_id}
  返回论文详情（含元数据 + 全文前 5000 字符）

GET /api/categories
  返回分类树
```

### 5. LLM 论文推荐

用户通过 Chat API 描述研究方向时，LLM 自动：
1. 从对话中提取关键研究方向关键词
2. 调用 `/api/papers/search` 搜索相关论文
3. 将搜索结果作为上下文返回给用户
4. 用户可选择将推荐的论文一键入库

此逻辑在 Chat Service 中实现，而非本 change 的核心。

## Risks / Trade-offs

- **arXiv API 速率限制**：API 要求请求间隔 ≥ 3 秒 → 使用指数退避重试策略
- **PDF 下载失败**：arXiv PDF 链接可能失效 → 异步任务记录失败状态，前端标记为"全文不可用"
- **Semantic Scholar 免费 API 限制**：100 请求/5 分钟 → 使用 Redis 记录调用计数

## Open Questions

- 是否需要支持 Google Scholar 爬虫？（暂不，法律风险和反爬问题）
- 分类体系是预定义还是用户自定义？（建议用户自定义 + arXiv 分类自动导入）
