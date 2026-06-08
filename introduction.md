# AstraLoom 项目介绍

## 一、项目概述

**AstraLoom**（AstraLoom 智能科研工作台）是一个面向学术研究团队的全栈、多用户 Web 平台。它将论文知识库管理、LLM 驱动的科研辅助、协作式研究思路生成、学术写作工具以及项目空间管理整合到一个可部署的应用中。系统采用 Docker Compose 自托管架构，适合团队在共享服务器上使用。

项目采用 **OpenSpec 规范驱动开发（SDD）** 方法论，每个功能特性均先由变更提案（change proposal）定义，审核通过后再实施，确保架构决策可追溯。

---

## 二、技术栈

### 2.1 后端

| 层级 | 技术 | 说明 |
|------|------|------|
| **语言** | Python 3.12+ | 全面异步 |
| **Web 框架** | FastAPI 0.115+ | ASGI，自动生成 API 文档 (`/docs`) |
| **ORM** | SQLAlchemy 2.0+ | 异步会话 (`AsyncSession`)，关系预加载 (`selectinload`) |
| **数据库** | PostgreSQL 16 + pgvector | 向量嵌入与业务数据同行存储 |
| **数据库迁移** | Alembic | 23 个迁移版本，位于 `backend/alembic/` |
| **任务队列** | Celery 5.4+ | Redis 作为 Broker 和结果后端 |
| **缓存/队列** | Redis 7 | 同时作为 Celery broker 和结果后端 |
| **LLM 集成** | LiteLLM 1.52+ | 统一接口对接 DeepSeek V4 Pro |
| **LLM 提供商** | DeepSeek V4 Pro | 支持思考/推理模式，100 万 Token 上下文 |
| **向量嵌入** | sentence-transformers (all-MiniLM-L6-v2) | 384 维，本地推理 |
| **词汇搜索** | rank-bm25 | 进程内 BM25 索引 |
| **交叉编码器** | cross-encoder/ms-marco-MiniLM-L-6-v2 | 重排序 |
| **学术 API** | arXiv Atom、Semantic Scholar Graph、OpenAlex、SerpApi (Google Scholar) | 多源论文发现 |
| **网络搜索** | Bing HTML、DuckDuckGo HTML、SearXNG、Tavily、Exa、Brave | 可配置的结构化 + 回退搜索 |
| **PDF 解析** | pdfplumber、PyMuPDF (fitz)、pikepdf | 多策略文本提取 |
| **文档导出** | python-docx | Word .docx 生成 |
| **认证** | JWT (python-jose) + bcrypt | 访问/刷新双 Token |

### 2.2 前端

| 层级 | 技术 | 说明 |
|------|------|------|
| **框架** | React 19 + TypeScript | Vite 8 构建 |
| **UI 库** | Ant Design 6 | 中文语言环境 (zh_CN) |
| **状态管理** | Zustand 5 | 认证、聊天、主题状态管理 |
| **PDF 渲染** | react-pdf (pdfjs-dist 5.4) | 浏览器端 PDF 查看器 |
| **Markdown/LaTeX** | react-markdown + rehype-katex + remark-gfm | GFM 表格 + KaTeX 数学公式 |
| **HTTP 客户端** | Axios | 带自动 Token 刷新拦截器 |

### 2.3 部署

| 层级 | 技术 | 说明 |
|------|------|------|
| **容器化** | Docker Compose | 开发 (`docker-compose.yml`) + 生产 (`docker-compose.prod.yml`) 配置 |
| **反向代理** | Nginx | 静态资源服务 + API 代理 |

**服务架构：** 7 个容器 —— PostgreSQL+pgvector、Redis、Backend (FastAPI)、Celery Worker、Celery Beat（定时调度）、Frontend (Nginx/Vite)、Nginx（反向代理）。

---

## 三、项目目录结构

```
AstraLoom/
├── backend/
│   ├── app/
│   │   ├── api/              # 18 个 API 路由模块
│   │   ├── core/             # 配置、安全、异常处理
│   │   ├── db/
│   │   │   ├── models/       # 9 个 ORM 模型
│   │   │   ├── session.py    # 异步数据库会话管理
│   │   │   └── init_db.py    # 启动初始化
│   │   ├── services/         # 38 个服务模块
│   │   │   └── agents/       # 5 个多智能体写作模块
│   │   ├── tasks/            # 3 个 Celery 任务模块
│   │   └── main.py           # FastAPI 入口
│   ├── alembic/              # 数据库迁移 (23 个版本)
│   ├── tests/                # 24 个测试文件
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # 通用组件 (AppLayout, Markdown, PDFViewer, ThinkingPanel, WorkflowStepGuide, WorkspaceResourceLinks 等)
│   │   ├── pages/            # 16 个页面组件
│   │   ├── services/         # Axios API 客户端 (含拦截器)
│   │   ├── stores/           # 4 个 Zustand Store
│   │   └── styles/           # home.css, responsive.css
│   ├── tests/                # 8 个契约测试
│   └── package.json
├── nginx/                    # nginx.conf, nginx.prod.conf
├── openspec/                 # OpenSpec 规范驱动开发产物
│   ├── project.md
│   ├── specs/                # 69 个功能规格
│   └── changes/              # 变更提案（设计文档，含归档）
└── docker-compose.yml
```

---

## 四、功能详解

### 4.1 论文知识库

**功能描述：** 自动搜索、发现、导入、分类和存储学术论文；提供对本地论文库的语义搜索和混合搜索。

**实现方式：**

- **论文搜索与发现** (`backend/app/services/paper_search.py`)：
  - 四个学术提供商适配器 —— `ArxivSearchService`（Atom API，含限速和 TTL 缓存）、`SemanticScholarService`（Graph API v1，90 次/5 分钟限速）、`OpenAlexService`（无需认证的公共 API，支持摘要倒排索引重构）、`GoogleScholarService`（基于 SerpApi，不直接抓取）。
  - 主函数 `search_scholarly_papers()` 按 `source` 参数分发到对应提供商。
  - `merge_provider_results()` 采用轮询方式合并结果以保证多样性。
  - `deduplicate_papers()` 通过 arxiv ID / DOI / 标题进行跨源去重。

- **论文导入** (`backend/app/services/paper_ingestion.py`)：
  - `PaperIngestionService` 接受 arxiv ID 或搜索查询，获取元数据，下载 PDF（可选自动下载），提取文本，存入 PostgreSQL。

- **混合搜索** (`backend/app/services/hybrid_search.py`)：
  - `HybridSearchService` 维护所有论文的进程内 BM25 索引（`rank-bm25`），在指纹不匹配时重建。
  - `search_hybrid()` 使用加权 RRF（Reciprocal Rank Fusion）融合 BM25 词汇分数和 pgvector 余弦相似度稠密分数，根据嵌入覆盖率自适应调整稠密权重。
  - 当覆盖率低于 80% 时回退到仅 BM25 搜索。
  - `RerankService` 加载 Cross-Encoder 模型（`cross-encoder/ms-marco-MiniLM-L-6-v2`）进行最终重排序。

- **向量嵌入** (`backend/app/services/embedding_service.py`)：
  - 懒加载 `SentenceTransformer('all-MiniLM-L6-v2')`，生成 384 维归一化嵌入向量，直接存储在 `papers.embedding`（pgvector 列）。

- **RAG 服务** (`backend/app/services/rag_service.py`)：
  - `RAGService.search_similar()` 先执行混合搜索，再进行交叉编码器重排序。
  - `build_rag_context()` 构造结构化上下文字符串，用于 LLM 注入。

- **论文增强** (`backend/app/services/paper_enhance.py`)：
  - 相似论文计算、保存/取消保存、阅读状态管理、个人笔记。

- **论文注释与阅读工作流** (`backend/app/services/paper_chunk_service.py`)：
  - 论文分块服务，支持基于块的 BM25 检索。
  - 用户论文注释（高亮、笔记、标签），阅读循环管理。

- **自动标签** (`backend/app/services/tagging_service.py`)：
  - 受 TopicGPT / LLM-TAKE 启发的 AI 驱动多级标签提取。

- **BibTeX/Zotero 导入** (`backend/app/api/papers.py`)：
  - 上传 `.bib` 或 Zotero CSV 文件，正则解析条目，创建 Paper 记录。

- **PDF 代理与镜像缓存** (`backend/app/services/arxiv_pdf_cache.py`，路由 `/papers/pdf-proxy/{arxiv_id}`)：
  - 服务端获取 arXiv PDF 以避免浏览器 CORS 问题。
  - 支持可配置的镜像 URL 列表，自动按优先级回退。

- **论文库维护中心**：管理员可一键补全缺失的论文全文和向量嵌入。

- **知识库检索评估** (`backend/app/services/retrieval_evaluation.py`)：
  - 检索质量基准测试，评估混合搜索和 RAG 的效果。

**数据模型** (`backend/app/db/models/paper.py`)：
- `Paper`：标题、作者（JSON）、年份、摘要、DOI、arxiv_id、来源、PDF 路径、全文、嵌入向量（Vector(384)）、标签（JSON）、分类（多对多，通过 `PaperCategory`）。
- `Category`：名称、描述、parent_id（自引用树形结构）。
- `UserPaper`：user_id、paper_id、是否保存、阅读状态、个人笔记、个人标签、论文聊天历史（JSON）、注释列表。
- `Folder`：名称、parent_id、user_id（嵌套文件夹树）。

**API 路由**（30+ 个端点）：
- `GET /api/papers/search` —— 统一搜索本地 + 远程（arXiv、Semantic Scholar、OpenAlex、Google Scholar）
- `GET /api/papers/semantic-search` —— 自然语言语义搜索
- `POST /api/papers/ingest` —— 通过 arxiv ID 或搜索导入论文
- `GET /api/papers/categories/tree` —— 分类树
- `GET /api/papers/{id}` —— 论文详情（含相似论文）
- `POST /api/papers/{id}/ask` + `/ask-stream` —— 基于 RAG 的论文问答
- `POST /api/papers/{id}/auto-tag` —— AI 标签提取
- `POST /api/papers/{id}/save`、`PUT /{id}/read-status` —— 个人论文库管理
- `GET /api/papers/pdf-proxy/{arxiv_id}` —— arXiv PDF 代理
- `POST /api/papers/import-bibtex`、`/import-zotero` —— 外部导入
- `GET /api/papers/search-evaluation` —— 检索基准测试
- `POST /api/papers/validate-citations` —— 引用验证
- `POST /api/papers/maintenance/backfill-full-text` —— 补全缺失全文（管理员）
- `POST /api/papers/maintenance/backfill-embeddings` —— 补全缺失向量（管理员）

---

### 4.2 AI 聊天 / 通用对话

**功能描述：** 类似 ChatGPT 的对话界面，支持多会话管理、RAG 增强聊天、文件上传（图片 + PDF）、网络搜索增强、流式响应（可选显示思考过程）。

**实现方式：**

- **LLM 服务** (`backend/app/services/llm.py`)：
  - `LLMService` 封装 `litellm.acompletion()`，含重试逻辑（最多 3 次，间隔 2 秒）。
  - 渐进式 max_tokens 升级（16384 → 32768 → 65536），解决 DeepSeek V4 Pro 的 `reasoning_content` 消耗全部预算导致无可见内容的问题。
  - `chat_stream()` —— 仅流式传输内容 Token（向后兼容）。
  - `chat_stream_with_thinking()` —— 流式传输结构化字典 `{"type": "reasoning"|"content"}`，供前端分离渲染。
  - `summarize_paper()` —— 结构化中文摘要（研究问题、方法、贡献、局限性、未来工作）。
  - 通过 `UsageTracker` 记录 Token 使用量。

- **聊天会话 API** (`backend/app/api/chat_sessions.py`)：
  - 会话和消息的 CRUD 操作。
  - `send_message` 和 `send_message_stream` 端点，支持 RAG 上下文注入（`_append_retrieval_context()`）、网络搜索增强、三级搜索深度（quick/standard/deep，可配置限制）。
  - 空流回退：如果模型未返回内容，发出恢复状态并使用"稳定模式"提示词重试。
  - 文件上传：图片（base64 编码，用于多模态模型）、PDF（多策略提取：pdfplumber → fitz → pikepdf+fitz）、文本文件。
  - 三层记忆架构（受 mem0/MemoryLLM/lethes 启发）：滑动窗口（最近 10 条消息）+ 超过 15 条消息时增量生成 LLM 摘要。

- **记忆服务** (`backend/app/services/memory_service.py`)：
  - `MemoryService.build_context()` 管理三层记忆。
  - `build_paper_context()` 使用分块论文检索（基于论文块的 BM25）代替全文注入以节省 Token。

- **数据模型** (`backend/app/db/models/chat.py`)：
  - `ChatSession`：user_id、标题、rag_enabled、消息列表。
  - `ChatMessage`：session_id、角色、内容、参考文献（JSON）。

- **前端** (`frontend/src/pages/ChatPage.tsx`)：
  - 会话列表侧边栏、流式消息显示、文件上传、RAG 开关、网络搜索开关、搜索深度选择器。
  - 空状态建议卡片，引导用户快速开始常见任务。
  - 思考面板 (`frontend/src/components/ThinkingPanel.tsx`)：带计时器的可折叠推理过程展示。
  - Markdown 渲染 (`frontend/src/components/Markdown.tsx`)：GFM 表格、KaTeX 数学公式、可复制代码块、样式化引用块。

---

### 4.3 研究思路工作台（Research Pipeline）

**功能描述：** 创建"研究项目"，通过多阶段流水线生成有证据支撑的研究思路，根据反馈演进思路，与 AI 讨论，生成实验代码。这是整个项目最核心的创新功能。

**实现方式：**

- **研究思路工作台服务** (`backend/app/services/research_idea_workbench.py`)：
  多阶段流水线，每个阶段都产生可追溯的中间产物：

  1. **简报阶段（Briefing）** —— 根据项目名称/描述/关键词编制项目简报
  2. **检索阶段（Retrieving）** —— 从本地论文库（种子/用户论文 + 混合搜索）和外部（arXiv + Semantic Scholar）收集证据
  3. **缺口映射阶段（Mapping Gaps）** —— LLM 根据证据生成结构化的研究缺口 JSON
  4. **生成阶段（Generating）** —— LLM 通过三条路径生成候选假设：
     - `grounded`（从研究缺口推导）
     - `inspiration`（跨论文组合灵感）
     - `seed_refinement`（用户种子细化）
  5. **去重阶段（Deduplicating）** —— 基于 Token-Jaccard 相似度（支持 CJK 二元组）去重
  6. **评审阶段（Reviewing）** —— 六维度 LLM 评审（新颖性、证据支撑、可行性、可测试性、影响力、清晰度），加权评分
  7. **选择阶段（Selecting）** —— 将 Top-N 提案持久化为 `ResearchIdea` 记录

  每个思路包含：假设、方法、新颖性、参考文献、证据图谱、评审 JSON、实验计划（数据集、基线、指标、步骤）、演化 JSON。

  `evolve_idea()` 基于实验反馈创建可追溯的子提案。

  所有 LLM 调用均使用 `_chat_json()` 强制 JSON 输出解析（含正则回退）。

- **研究 Idea 验证循环**：
  - 支持对生成的 Idea 进行多轮验证反馈。
  - 基于证据的评估，追踪 Idea 从草案到验证通过的全过程。

- **论文收藏驱动研究**：
  - 将论文收藏（UserPaper 集合）直接作为研究方向种子。
  - 自动分析收藏覆盖度，推荐补充论文以填补研究缺口。

- **研究实验执行包**：
  - 为已验证的 Idea 生成可执行的实验方案（数据集、基线、评估指标、代码骨架）。

- **研究流水线服务** (`backend/app/services/research_service.py`)：
  - 思路讨论、代码生成的遗留流水线服务。

- **论文选择** (`backend/app/services/paper_selection.py`)：
  - 为项目主题推荐相关论文。

- **每日摘要服务** (`backend/app/services/digest_service.py`)：
  - 每日 arXiv 摘要获取/生成、实验日志记录、分享。

- **API** (`backend/app/api/research.py`，约 780 行)：
  - 研究项目和思路的 CRUD 操作
  - `POST /projects/{id}/generate-ideas`（遗留）、`/idea-runs/stream`（SSE 流式）
  - `POST /ideas/{id}/evolve`、`/evolve-from-feedback` —— 思路演进
  - `POST /ideas/{id}/generate-code` —— 生成 PyTorch 代码
  - `POST /ideas/compare` —— 多思路并排比较
  - `GET /ideas/{id}/lineage` —— 祖先/后代树
  - `POST /projects/{id}/share` —— 生成分享链接
  - `POST /arxiv-digest` —— 每日 arXiv 摘要

- **数据模型** (`backend/app/db/models/research.py`)：
  - `ResearchProject`：名称、描述、关键词、paper_ids（JSON）、状态、user_id
  - `ResearchIdeaRun`：project_id、状态、阶段、进度、config_json、evidence_map、gap_map、candidate_pool、review_summary
  - `ResearchIdea`：project_id、generation_run_id、parent_idea_id、标题、描述、假设、方法、新颖性、可行性评分、新颖性评分、参考文献、evidence_json、review_json、experiment_plan、evolution_json、generated_code、discussion_log

---

### 4.4 写作助手（V1 + V2 多智能体流水线）

**功能描述：** AI 驱动的学术写作辅助：引用推荐、相关工作生成、文本润色、摘要生成、文献综述、论文对比、小组报告生成、NSFC 基金申请书撰写、多格式导出。

**V1 API** (`backend/app/api/writing.py`)：
- `POST /writing/recommend-citations` —— 基于语义相似度的引文推荐（含 BibTeX）
- `POST /writing/related-work` —— LLM 根据知识库生成相关工作章节
- `POST /writing/polish` —— 学术/简洁/流畅/英文润色
- `POST /writing/generate-abstract` —— 结构化摘要生成
- `POST /writing/literature-review` —— 完整文献综述（含对比表格）
- `POST /writing/compare-papers` —— 多论文方法/数据/结果对比
- `POST /writing/group-report` —— 生成 Word .docx 小组会议报告
- `POST /writing/group-report-to-feishu` —— 报告写入飞书文档
- `POST /writing/grant/write-section`、`/grant/review-section`、`/grant/extract-innovation`、`/grant/polish` —— NSFC 基金申请书辅助

**V2 多智能体流水线** (`backend/app/services/writing_pipeline.py`)：
- `WritingPipeline` 通过 SSE 流式协调 5 个专业智能体有序执行：

| 智能体 | 功能 | 实现文件 |
|--------|------|----------|
| **Selector Agent** | 从知识库中检索相关论文，构建论文列表记录在 WorkingMemory 中 | `selector_agent.py` |
| **Reader Agent** | 阅读选定论文，提取研究问题/方法/结果，构建阅读笔记 | `reader_agent.py` |
| **Writer Agent** | 根据 7 种任务特定提示词生成内容（含思考支持） | `writer_agent.py` |
| **Reviewer Agent** | 评审写作输出，从清晰度/完整性/正确性/引用四维度评估并建议改进 | `reviewer_agent.py` |
| **Citation Agent** | 格式化内联引用，构建参考文献列表，与知识库交叉验证，生成 BibTeX | `citation_agent.py` |

- **按任务类型配置阶段**：润色只需 Writer+Reviewer；相关工作需要 Selector+Reader+Writer+Citation；完整章节需要全部 5 个智能体。
- `WorkingMemory` 在智能体间共享：包含 papers、reading_notes、writer_output、citation_map。
- `PipelineEvent` SSE 流式传输，实现前端实时进度展示。

**写作工作台重构**（写作 V2 API `backend/app/api/writing_v2.py`）：
- `POST /writing/pipeline/stream` —— 统一流式流水线端点
- `POST /writing/polish/diff` —— 基于差异的润色（compute_diff、unified_diff）
- `POST /writing/polish/apply-diff` —— 接受/拒绝单个差异块
- `POST /writing/citations/verify` —— 引文验证
- `POST /writing/citations/smart-recommend` —— 上下文感知引文推荐
- `POST /writing/latex/import` —— 导入 .tex 文件作为写作项目
- `POST /writing/latex/compile-check` —— LaTeX 编译检查
- 写作项目 CRUD，支持模板（空白、ACL、CVPR、NeurIPS、ICML、NSFC）
- 多格式导出：Markdown、LaTeX、Word .docx

**草稿质量教练**：对写作草稿进行多维度质量评估，给出具体改进建议。

**引用决策循环**：闭环验证 AI 生成的引文 —— 检索 → 交叉验证 → 修正或替换，确保引用准确性。

**差异引擎** (`backend/app/services/diff_engine.py`)：
- 计算原文与润色后文本的行级差异
- 支持逐块接受/拒绝和版本历史

**引文验证器** (`backend/app/services/citation_verifier.py`)：
- 验证 AI 生成的引文，通过搜索知识库确认其真实性

**智能引文服务** (`backend/app/services/smart_citation_service.py`)：
- 上下文感知的引文推荐，分析写作上下文后推荐最相关的论文

**LaTeX 处理器** (`backend/app/services/latex_processor.py`)：
- 从 .tex 文件中提取章节
- 提取参考文献路径
- 使用 latex/base Docker 镜像进行编译检查

**写作项目服务** (`backend/app/services/writing_project_service.py`)：
- 项目 CRUD、章节管理、模板系统（6 种模板）、多格式导出
- 支持将写作项目绑定到研究方向上下文（Research-to-Writing Evidence Bridge）

**数据模型** (`backend/app/db/models/writing.py`)：
- `WritingProject`：user_id、标题、描述、模板类型、状态、metadata_json、章节列表
- `WritingSection`：project_id、标题、内容、排序、状态、字数、润色版本列表
- `PolishVersion`：section_id、原文、润色后文本、diff_json、版本号、用户操作记录

---

### 4.5 项目空间（Workspaces / Project Spaces）

**功能描述：** 统一科研项目空间 —— 将论文、研究方向、写作草稿和团队成员整合到同一协作工作台，提供进度看板、资源绑定、活动日志和下一步建议。这是 v2 版本最核心的新增功能。

**实现方式** (`backend/app/api/workspaces.py`, `backend/app/services/workspace_service.py`)：

- **空间管理**：
  - 创建/编辑/删除项目空间，设置名称和描述。
  - 支持 owner、editor、viewer 三种角色。

- **成员管理**：
  - 通过用户名或邮箱添加成员，指定 editor 或 viewer 角色。
  - Owner 可以移除成员。

- **资源绑定**：
  - 将论文（papers）、研究方向（research_projects）、写作草稿（writing_projects）绑定到空间。
  - 资源候选搜索（按标题/描述检索）。
  - 支持手动输入资源 ID 绑定。

- **资源反向链接**：在任何论文详情、研究方向页或写作项目页，可以查看该资源已关联的项目空间，支持从详情页直接加入或移出空间。

- **活动日志**：记录空间内所有操作（创建、更新、成员变更、资源绑定/移除），显示在空间详情页的时间线中。

- **研究看板**：自动计算推进进度分数、阶段标签，展示绑定资源的统计卡片。

- **下一步建议**：基于空间内当前资源覆盖情况，自动推荐下一步动作。

- **启动台组件** (`frontend/src/components/WorkflowStepGuide.tsx`)：提供分步骤的工作流引导卡片，标注推荐下一步 / 可执行 / 可选 / 需准备等状态。

- **空间间资源关联** (`frontend/src/components/WorkspaceResourceLinks.tsx`)：在论文/研究方向/写作项目详情页显示关联空间，支持一键加入或移出。

**数据模型** (`backend/app/db/models/workspace.py`)：
- `ProjectSpace`：名称、描述、owner_id、状态、metadata_json、成员列表、资源列表、活动列表。
- `ProjectSpaceMember`：space_id、user_id、角色（owner/editor/viewer）。
- `ProjectSpaceResource`：space_id、resource_type、resource_id、added_by。
- `ProjectSpaceActivity`：space_id、actor_id、action、resource_type、resource_id、metadata_json。

**API 路由**（10+ 端点）：
- `POST /api/workspaces` —— 创建空间
- `GET /api/workspaces` —— 列出空间（含摘要、看板数据）
- `GET /api/workspaces/{id}` —— 空间详情（含看板、下一步建议、活动日志）
- `PATCH /api/workspaces/{id}` —— 编辑空间
- `DELETE /api/workspaces/{id}` —— 删除空间
- `POST /api/workspaces/{id}/members` —— 添加成员
- `DELETE /api/workspaces/{id}/members/{user_id}` —— 移除成员
- `GET /api/workspaces/{id}/activities` —— 空间活动日志
- `GET /api/workspaces/{id}/resource-candidates` —— 候选资源搜索
- `POST /api/workspaces/{id}/resources` —— 绑定资源
- `DELETE /api/workspaces/{id}/resources/{type}/{id}` —— 解绑资源
- `GET /api/workspaces/resource-links` —— 资源反向链接查询

**前端页面**：
- `WorkspacesPage.tsx` —— 空间列表页，展示每个空间的名称、角色标签、成员数、推进进度条、资源计数。
- `WorkspaceDetailPage.tsx` —— 空间详情页，含启动台引导、看板统计卡片、资源列表、成员管理、活动时间线、资源绑定面板。

---

### 4.6 跨模块行动中心

**功能描述：** 自动扫描论文库、研究方向、写作项目和项目空间的状态，生成优先级排名的下一步行动建议。支持直接执行 API 动作（如补全缺失全文）。

**实现方式** (`backend/app/api/workflow.py`, `backend/app/services/workflow_action_service.py`)：

- **智能扫描**：逐一检查各模块状态 ——
  - 论文：是否有收藏论文、未读论文数、缺失全文/向量数
  - 推送：是否有未读论文摘要
  - 研究：是否有活跃研究方向、草稿 Idea 数
  - 写作：是否有草稿写作项目
  - 空间：是否有参与的项目空间

- **行动生成**：为每个状态生成具体的行动项，含优先级（high/medium/low）、描述、跳转路径和可执行 API 端点。

- **直接执行**：知识库维护类行动（补全文、补向量）可直接在行动中心执行，无需跳转。

- **分组展示**：按论文与知识库、研究方向、写作助手、项目空间四大模块分组。

**前端页面** (`frontend/src/pages/ActionCenterPage.tsx`)：
- 顶部统计卡片（总行动项数、高优先级数）
- 按模块分组展示行动列表，支持一键进入或执行。

---

### 4.7 管理员后台

**功能描述：** 系统管理员治理面板 —— 用户权限管理、项目空间概览、系统统计。

**实现方式** (`backend/app/api/admin.py`)：

- **总览仪表盘**：用户数、活跃用户数、管理员数、论文数、研究方向数、写作项目数、项目空间数统计。
- **风险提示**：自动检测治理风险（如仅 1 个管理员、0 个项目空间）。
- **用户管理**：搜索用户、修改角色（user/admin）、启停账号（带保护规则 —— 不能删除最后一个活跃管理员）。
- **项目空间治理**：查看所有空间、所有者、成员分布、角色分布、状态。
- **空间活动监控**：查看最近的空间活动时间线。

**前端页面** (`frontend/src/pages/AdminPage.tsx`)：
- 权限检查，无管理员权限时展示警告。
- 统计卡片、用户表格（含行内角色切换和启停开关）、空间表格、活动时间线。

---

### 4.8 论文推送中心

**功能描述：** 基于用户订阅关键词的每日 arXiv 论文推送，提供反馈循环以优化推荐排序。用户可以直接从推送中一键入库、加入待读或开始阅读。

**实现方式**：

- **订阅管理** (`backend/app/api/notifications.py`)：
  - 每个用户可配置 up to 20 个关注关键词。
  - 支持每日推送频率、自定义发送时间段（send_hour）。
  - 关键词归一化（去重、截断、保留原始顺序）。

- **推送生成** (`backend/app/services/digest_service.py`)：
  - 根据关键词搜索 arXiv，LLM 总结后生成 Markdown 摘要。
  - 每篇推荐论文包含推荐分数和推荐理由。

- **反馈循环**：用户可对每篇推送论文标记「感兴趣」「稍后阅读」「不感兴趣」，反馈数据存入 metadata，供后续排序优化。

- **自定义排名** (`backend/app/services/digest_service.py`)：根据用户历史反馈个性化调整推荐排序。

- **测试推送**：用户可以立即触发一条测试推送，验证订阅链路。

**前端页面** (`frontend/src/pages/PaperDigestInboxPage.tsx`)：
- 推送历史列表，未读推送高亮显示。
- 每篇推送论文展示元数据（年份、作者、arXiv ID、推荐分、推荐理由、摘要）。
- 一键操作：加入论文库、加入待读列表、开始阅读（跳转详情页）、感兴趣/稍后/不感兴趣反馈。

---

### 4.9 网络搜索增强

**功能描述：** 可配置的多提供商网络搜索，用实时互联网结果增强聊天和论文问答。

**实现方式** (`backend/app/services/web_search.py`)：
- **结构化提供商**（优先配置）：SearXNG（自托管）、Tavily API、Exa API、Brave Search API
- **HTML 回退**（始终可用）：Bing（HTML 解析 + RSS）、DuckDuckGo HTML
- `plan_search_queries()` 根据搜索深度生成确定性查询变体（quick=1 个、standard=3 个、deep=5 个），含语言感知后缀
- `search_web_results()` 并发执行所有已配置提供商的所有查询变体，按规范 URL 去重，不足时用 HTML 回退补充
- `format_web_context()` 生成 `[WEB-N]` 前缀的 Markdown 格式，用于 LLM 注入
- `WebSearchResult` 数据类，含 `as_reference()` 方法用于结构化来源归属
- 通过环境变量配置：`SEARXNG_API_URL`、`TAVILY_API_KEY`、`EXA_API_KEY`、`BRAVE_SEARCH_API_KEY`

---

### 4.10 前端界面

**功能描述：** 完整的单页应用（SPA），支持响应式布局、多主题、键盘快捷键、统一工作流引导。

**实现方式：**

- **路由** (`frontend/src/App.tsx`)：
  - React Router，16 个路由：公开首页（全屏）、认证页面（登录/注册）、应用布局页面（侧边栏）——聊天、行动中心、论文、论文推送、论文详情、研究、研究详情、写作、项目空间列表、项目空间详情、管理员后台、设置。

- **应用布局** (`frontend/src/components/AppLayout.tsx`)：
  - 可折叠侧边栏，渐变 Logo，7 个导航项（行动中心、聊天、论文、研究、写作、项目空间、设置）
  - 通知铃铛（轮询未读数）、主题切换器、用户头像/下拉菜单
  - 键盘快捷键弹窗（`?`），响应式移动端抽屉导航

- **键盘快捷键**：`Ctrl+K` 搜索论文、`Ctrl+N` 新对话、`Ctrl+B` 返回、`Ctrl+H` 首页、`?` 显示全部快捷键

- **状态管理**（4 个 Zustand Store）：
  - `useAuthStore` —— JWT Token 管理、自动刷新、用户资料
  - `useChatSessionStore` —— 会话、消息、流式传输、RAG/网络搜索开关
  - `useChatStore` —— 简单聊天状态
  - `useThemeStore` —— 多主题预设（neon、aurora、forest、ocean、sunset、tokyo、lavender）

- **API 客户端** (`frontend/src/services/api.ts`)：
  - Axios 拦截器：自动注入 JWT、网络重试（1 次）、自动 401 → refresh_token → 重试链路

- **通用组件**：
  - `Markdown.tsx` —— GFM + KaTeX + 代码复制 + 样式化引用块
  - `PDFViewer.tsx` —— react-pdf 渲染，页码导航，文本选择回调（"询问选中内容"）
  - `ThinkingPanel.tsx` —— 可折叠推理过程，实时计时器
  - `WorkflowStepGuide.tsx` —— 统一工作流步骤引导组件（推荐下一步 / 可执行 / 可选 / 需准备）
  - `WorkspaceResourceLinks.tsx` —— 资源详情页的空间关联组件
  - `writing/` 子组件：`PipelineProgress.tsx`（SSE 阶段进度）、`DiffViewer.tsx`、`SectionEditor.tsx`、`WritingProjectPanel.tsx`、`CitationVerifyBadge.tsx`

- **页面组件**（16 个）：
  - `HomePage.tsx` —— 着陆页/英雄页
  - `ChatPage.tsx` ——（最大页面）多会话聊天，流式传输，文件上传，RAG/网络搜索控制，搜索深度选择器，提示词快捷方式
  - `ActionCenterPage.tsx` —— 跨模块下一步行动建议，支持直接执行 API 动作
  - `PapersPage.tsx` —— 搜索/发现/导入论文，已保存/阅读集合，小组报告生成
  - `PaperDetailPage.tsx` —— 论文元数据 + PDF 查看器 + 论文聊天 + 文本选择 → AI 解释 + 空间关联
  - `PaperDigestInboxPage.tsx` —— 论文推送中心，历史摘要 + 论文操作 + 反馈
  - `ResearchPage.tsx` / `ResearchProjectPage.tsx` —— 思路工作台 UI
  - `WritingPage.tsx` —— 写作工具 + 项目管理
  - `WorkspacesPage.tsx` —— 项目空间列表，含进度条和资源计数
  - `WorkspaceDetailPage.tsx` —— 空间详情，含启动台、看板、资源管理、活动时间线
  - `LoginPage.tsx` / `RegisterPage.tsx` —— 认证表单
  - `SettingsPage.tsx` —— 个人资料、密码、API 配置、推送订阅设置
  - `AdminPage.tsx` —— 管理员后台

- **响应式设计** (`frontend/src/styles/responsive.css`)：
  - 移动端友好，抽屉导航，断点感知组件

---

### 4.11 认证与多用户

**实现方式** (`backend/app/core/security.py`)：
- JWT 使用 HS256 算法：30 分钟访问 Token，7 天刷新 Token
- bcrypt 密码哈希（截断至 72 字节，符合 bcrypt 限制）
- 三种依赖注入守卫：
  - `get_current_user` —— 未认证返回 401
  - `get_optional_user` —— 未认证返回 None
  - `require_admin` —— 非管理员返回 403
- Token 刷新流程：前端 Axios 拦截器在收到 401 时自动刷新

**数据模型** (`backend/app/db/models/user.py`)：
- `User`：username（唯一）、email（唯一）、hashed_password、role（user/admin）、is_active、avatar（base64）、display_name

---

### 4.12 可观测性与管理功能

**实现方式：**

- **用量追踪** (`backend/app/services/usage_tracker.py`)：
  - `TokenUsage` 模型记录每次 LLM 调用的 prompt/completion/total tokens、模型、端点、费用估算。
  - `UsageTracker` 聚合每个用户和全局的统计信息。
  - API：个人用量统计 (`/api/usage/my-stats`)、全量统计 (`/api/usage/all-stats`，管理员)、调用历史 (`/api/usage/history`)。

- **通知** (`backend/app/api/notifications.py`)：
  - 摘要订阅（基于关键词的 arXiv 提醒）、系统通知（已读/未读跟踪）、推送反馈、测试推送。

- **设置** (`backend/app/api/settings.py`)：
  - 个人资料编辑、头像上传（base64）、密码修改、API 配置展示（密钥已脱敏）、可用网络搜索提供商列表。

---

### 4.13 后台任务队列

**实现方式** (`backend/app/tasks/`)：
- `celery_app.py` —— Celery 应用配置，Redis Broker
- `paper_tasks.py` —— 异步任务：`download_paper`（从 arXiv 下载）、`parse_pdf`（提取文本）、`generate_embedding`（向量化）
- `daily_digest.py` —— 为订阅用户定时生成 arXiv 每日摘要，支持可配置的 send_hour
- Celery Beat 定时调度器（独立容器），管理周期性任务
- **API** (`backend/app/api/tasks.py`)：提交和查询任务状态（使用 Celery `AsyncResult`）

---

### 4.14 全文加载与小组报告

**实现方式：**

- **PDF 全文加载** (`backend/app/services/report_service.py`)：
  - `ensure_full_text()` 异步从 arXiv 下载 PDF（httpx），用 pdfplumber/fitz 提取文本，缓存至数据库。
  - 在论文详情页触发后台预加载。
  - 管理员可一键批量补全缺失全文。

- **小组报告** (`backend/app/services/report_service.py`)：
  - `ReportService.generate_report()` 接收论文 ID 列表，调用 LLM 对每篇论文进行结构化分析（问题/方法/结果/优势/不足），返回 Markdown，并通过 python-docx 生成 .docx 文件。

- **飞书集成** (`backend/app/services/feishu_service.py`)：
  - 通过飞书（Lark）API 将报告写入飞书文档。

- **出版物导出包**：支持将论文和写作项目导出为标准学术出版格式。

---

## 五、测试

项目包含 24 个后端测试文件和 8 个前端测试文件：

### 5.1 后端测试

| 测试文件 | 测试范围 |
|----------|----------|
| `test_paper_discovery_search_and_ingest.py` | 论文搜索和导入工作流 |
| `test_paper_full_text_reliability.py` | 全文加载鲁棒性 |
| `test_paper_detail_chat_parity.py` | 论文问答一致性 |
| `test_paper_reader_grounded_interaction.py` | 基于证据的论文阅读交互 |
| `test_paper_reading_workflow.py` | 论文阅读工作流 |
| `test_paper_annotations.py` | 论文注释功能 |
| `test_scholarly_source_pdf_and_google_scholar.py` | 学术源可靠性 |
| `test_arxiv_pdf_mirror_cache.py` | arXiv PDF 镜像缓存 |
| `test_chat_retrieval_mode_coordination.py` | RAG/网络搜索检索协调 |
| `test_streamed_chat_empty_response_protection.py` | 空响应处理 |
| `test_web_search_reliability.py` | 网络搜索鲁棒性 |
| `test_core_workflow_stabilization.py` | 核心工作流稳定性 |
| `test_multi_user_authorization_boundaries.py` | 多用户认证边界 |
| `test_profile_identity_sync.py` | 个人资料一致性 |
| `test_research_idea_workbench.py` | 研究思路工作台流水线 |
| `test_retrieval_quality_evaluation.py` | 检索质量基准 |
| `test_knowledge_base_maintenance.py` | 知识库维护 |
| `test_writing_assistant_v2.py` | 写作助手 V2 |
| `test_writing_closed_loop.py` | 写作闭环验证 |
| `test_workspace_project_spaces.py` | 项目空间功能 |
| `test_workspace_resource_access_control.py` | 空间资源访问控制 |
| `test_admin_workspace_governance.py` | 管理员空间治理 |
| `test_cross_module_action_center.py` | 跨模块行动中心 |
| `test_notification_digest_center.py` | 通知与摘要中心 |

### 5.2 前端测试

| 测试文件 | 测试范围 |
|----------|----------|
| `app-layout-contract.test.mjs` | 前端布局契约测试 |
| `action-center-contract.test.mjs` | 行动中心契约测试 |
| `paper-collections-contract.test.mjs` | 论文收藏契约测试 |
| `research-idea-validation-contract.test.mjs` | 研究 Idea 验证契约测试 |
| `settings-subscription-contract.test.mjs` | 设置与订阅契约测试 |
| `workflow-step-guide-contract.test.mjs` | 工作流引导契约测试 |
| `workspace-launchpad-contract.test.mjs` | 空间启动台契约测试 |
| `writing-workbench-contract.test.mjs` | 写作工作台契约测试 |

---

## 六、部署架构

系统通过 Docker Compose 编排 7 个服务：

```
┌─────────────────────────────────────────────────────────┐
│                         Nginx                            │
│                 (反向代理 + 静态资源)                       │
└──────┬─────────────────────────────┬────────────────────┘
       │                             │
       ▼                             ▼
┌──────────────┐           ┌──────────────────────┐
│   Frontend   │           │   Backend (FastAPI)    │
│  (静态页面)   │           │    (API 服务)          │
└──────────────┘           └────┬──────┬───────────┘
                                │      │
                       ┌────────▼──┐ ┌─▼──────────────┐
                       │ PostgreSQL │ │     Redis      │
                       │ + pgvector │ │ (Broker +      │
                       │            │ │  Cache)        │
                       └────────────┘ └────┬───────────┘
                                           │
                              ┌────────────▼──────────┐
                              │    Celery Worker       │
                              │  (异步任务处理)         │
                              └────────────────────────┘
                              ┌────────────────────────┐
                              │    Celery Beat          │
                              │  (定时任务调度)          │
                              └────────────────────────┘
```

- **开发环境**：使用 `docker-compose.yml`，支持热重载，前端 Vite 开发服务器
- **生产环境**：使用 `docker-compose.prod.yml` 覆盖配置，启用 HTTPS、收紧安全策略

---

## 七、数据模型总览

| 模型 | 表名 | 说明 |
|------|------|------|
| `User` | `users` | 用户账户、角色、认证信息 |
| `Paper` | `papers` | 论文元数据、全文、向量嵌入 (384 维) |
| `Category` | `categories` | 论文分类树 |
| `UserPaper` | `user_papers` | 用户-论文关联（收藏、阅读状态、笔记、注释） |
| `Folder` | `folders` | 用户论文文件夹（嵌套树） |
| `ChatSession` | `chat_sessions` | 聊天会话 |
| `ChatMessage` | `chat_messages` | 聊天消息（含引用） |
| `ResearchProject` | `research_projects` | 研究方向项目 |
| `ResearchIdea` | `research_ideas` | 研究思路（含父级谱系） |
| `ResearchIdeaRun` | `research_idea_runs` | 思路生成运行记录 |
| `WritingProject` | `writing_projects` | 写作项目 |
| `WritingSection` | `writing_sections` | 写作章节 |
| `PolishVersion` | `polish_versions` | 润色版本历史 |
| `ProjectSpace` | `project_spaces` | 项目协作空间 |
| `ProjectSpaceMember` | `project_space_members` | 空间成员 |
| `ProjectSpaceResource` | `project_space_resources` | 空间-资源绑定 |
| `ProjectSpaceActivity` | `project_space_activities` | 空间活动日志 |
| `DigestSubscription` | `digest_subscriptions` | 论文推送订阅 |
| `Notification` | `notifications` | 系统通知/推送 |
| `TokenUsage` | `token_usages` | LLM Token 用量记录 |

---

## 八、OpenSpec 规范体系

项目采用 OpenSpec 规范驱动开发，当前共有 **69 个功能规格** 覆盖以下领域：

- **论文**（14 个规格）：搜索、发现、导入、全文、注释、阅读、推送、检索评估等
- **聊天**（5 个规格）：检索协调、网络搜索、思考展示、空响应保护等
- **研究**（7 个规格）：思路生成、证据与演进、验证循环、实验执行、收藏驱动等
- **写作**（10 个规格）：多智能体流水线、闭环验证、引用决策、草稿质量、投稿模板、证据桥接等
- **项目空间**（8 个规格）：统一流、启动台、看板、资源管理、访问控制、活动日志、管理治理等
- **认证**（3 个规格）：认证 API、中间件、前端
- **基础设施**（12+ 个规格）：混合搜索、网络搜索、部署、响应式、TypeScript 质量门等
- **跨模块**（10+ 个规格）：行动中心、工作流引导、布局边界、个人资料同步等

---

## 九、总结

AstraLoom 是一个功能完备、面向学术研究团队的生产级平台，其核心特色包括：

1. **多源论文发现** —— 4 个学术 API + 2 种导入格式 + PDF 镜像缓存代理，全部去重
2. **深度混合搜索** —— BM25 + pgvector 稠密向量 + 交叉编码器重排序，自适应融合
3. **有证据支撑的思路生成** —— 创新的 7 阶段流水线：收集证据 → 映射研究缺口 → 多路径生成假设 → 六维度评审 → 可追溯的全过程产物，含验证循环和实验执行包
4. **多智能体写作流水线** —— 5 个专业智能体（选择、阅读、写作、评审、引文）通过 SSE 协调，带版本控制的差异润色、引文验证闭环、草稿质量教练
5. **统一项目空间** —— 将论文、研究方向、写作草稿和团队成员整合到同一协作工作台，含进度看板、资源绑定、活动日志和下一步建议
6. **跨模块行动中心** —— 自动扫描各模块状态，生成优先级排名行动建议，支持一键执行维护动作
7. **管理员治理台** —— 用户权限管理、项目空间概览、系统统计与风险提示
8. **个性化论文推送** —— 基于关键词订阅的每日 arXiv 摘要，含反馈循环优化推荐排序
9. **多源网络搜索** —— 4 个结构化 API 提供商 + 2 个 HTML 回退，含查询规划和去重
10. **生产级部署** —— Docker Compose 7 服务编排（含 Celery Beat 定时调度），支持开发和生产配置
11. **全面的测试覆盖** —— 24 个后端测试 + 8 个前端契约测试
12. **中文优先体验** —— Ant Design zh_CN、中文论文处理、NSFC 基金申请支持
