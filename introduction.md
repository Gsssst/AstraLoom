# Auto-Research-DS 项目介绍

## 一、项目概述

**Auto-Research-DS**（自动化研究流程系统）是一个面向学术研究团队的全栈、多用户 Web 平台。它将论文知识库管理、LLM 驱动的科研辅助、协作式研究思路生成以及学术写作工具整合到一个可部署的应用中。系统采用 Docker Compose 自托管架构，适合团队在共享服务器上使用。

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
| **数据库迁移** | Alembic | 位于 `backend/alembic/` |
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
| **框架** | React 19 + TypeScript 6 | Vite 8 构建 |
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

**服务架构：** 5 个容器 —— PostgreSQL+pgvector、Redis、Backend (FastAPI)、Celery Worker、Frontend (Nginx)。

---

## 三、项目目录结构

```
auto-Research-DS/
├── backend/
│   ├── app/
│   │   ├── api/              # 12 个 API 路由模块
│   │   ├── core/             # 配置、安全、异常处理
│   │   ├── db/
│   │   │   ├── models/       # 7 个 ORM 模型
│   │   │   ├── session.py    # 异步数据库会话管理
│   │   │   └── init_db.py    # 启动初始化
│   │   ├── services/         # 28 个服务模块
│   │   │   └── agents/       # 5 个多智能体写作模块
│   │   ├── tasks/            # 3 个 Celery 任务模块
│   │   ├── evaluation/       # 检索评估模块
│   │   └── main.py           # FastAPI 入口
│   ├── alembic/              # 数据库迁移
│   ├── tests/                # 13 个测试文件
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # 通用组件 (AppLayout, Markdown, PDFViewer, ThinkingPanel 等)
│   │   ├── pages/            # 11 个页面组件
│   │   ├── services/         # Axios API 客户端 (含拦截器)
│   │   ├── stores/           # 4 个 Zustand Store
│   │   └── styles/           # home.css, responsive.css
│   └── package.json
├── nginx/                    # nginx.conf, nginx.prod.conf
├── openspec/                 # OpenSpec 规范驱动开发产物
│   ├── project.md
│   ├── specs/
│   └── changes/              # ~30 个变更提案（设计文档）
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

- **自动标签** (`backend/app/services/tagging_service.py`)：
  - 受 TopicGPT / LLM-TAKE 启发的 AI 驱动多级标签提取。

- **BibTeX/Zotero 导入** (`backend/app/api/papers.py`)：
  - 上传 `.bib` 或 Zotero CSV 文件，正则解析条目，创建 Paper 记录。

- **PDF 代理** (`backend/app/api/papers.py` 路由 `/papers/pdf-proxy/{arxiv_id}`)：
  - 服务端获取 arXiv PDF 以避免浏览器 CORS 问题。

**数据模型** (`backend/app/db/models/paper.py`)：
- `Paper`：标题、作者（JSON）、年份、摘要、DOI、arxiv_id、来源、PDF 路径、全文、嵌入向量（Vector(384)）、标签（JSON）、分类（多对多，通过 `PaperCategory`）。
- `Category`：名称、描述、parent_id（自引用树形结构）。
- `UserPaper`：user_id、paper_id、是否保存、阅读状态、个人笔记、个人标签、论文聊天历史（JSON）。
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

**V2 API** (`backend/app/api/writing_v2.py`)：
- `POST /writing/pipeline/stream` —— 统一流式流水线端点
- `POST /writing/polish/diff` —— 基于差异的润色（compute_diff、unified_diff）
- `POST /writing/polish/apply-diff` —— 接受/拒绝单个差异块
- `POST /writing/citations/verify` —— 引文验证
- `POST /writing/citations/smart-recommend` —— 上下文感知引文推荐
- `POST /writing/latex/import` —— 导入 .tex 文件作为写作项目
- `POST /writing/latex/compile-check` —— LaTeX 编译检查
- 写作项目 CRUD，支持模板（空白、ACL、CVPR、NeurIPS、ICML、NSFC）
- 多格式导出：Markdown、LaTeX、Word .docx

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

**数据模型** (`backend/app/db/models/writing.py`)：
- `WritingProject`：user_id、标题、描述、模板类型、状态、metadata_json、章节列表
- `WritingSection`：project_id、标题、内容、排序、状态、字数、润色版本列表
- `PolishVersion`：section_id、原文、润色后文本、diff_json、版本号、用户操作记录

---

### 4.5 网络搜索增强

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

### 4.6 前端界面

**功能描述：** 完整的单页应用（SPA），支持响应式布局、多主题、键盘快捷键。

**实现方式：**

- **路由** (`frontend/src/App.tsx`)：
  - React Router：公开首页（全屏）、认证页面（登录/注册）、应用布局页面（侧边栏）——聊天、论文、研究、写作、设置。

- **应用布局** (`frontend/src/components/AppLayout.tsx`)：
  - 可折叠侧边栏，渐变 Logo，5 个导航项（聊天、论文、研究、写作、设置）
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
  - `writing/` 子组件：`PipelineProgress.tsx`（SSE 阶段进度）、`DiffViewer.tsx`、`SectionEditor.tsx`、`WritingProjectPanel.tsx`、`CitationVerifyBadge.tsx`

- **页面组件**（11 个）：
  - `HomePage.tsx` —— 着陆页/英雄页
  - `ChatPage.tsx` ——（最大页面）多会话聊天，流式传输，文件上传，RAG/网络搜索控制，搜索深度选择器，提示词快捷方式
  - `PapersPage.tsx` —— 搜索/发现/导入论文，已保存/阅读集合，小组报告生成
  - `PaperDetailPage.tsx` —— 论文元数据 + PDF 查看器 + 论文聊天 + 文本选择 → AI 解释
  - `ResearchPage.tsx` / `ResearchProjectPage.tsx` —— 思路工作台 UI
  - `WritingPage.tsx` —— 写作工具（8 个功能卡片）+ 项目管理
  - `LoginPage.tsx` / `RegisterPage.tsx` —— 认证表单
  - `SettingsPage.tsx` —— 个人资料、密码、API 配置展示

- **响应式设计** (`frontend/src/styles/responsive.css`)：
  - 移动端友好，抽屉导航，断点感知组件

---

### 4.7 认证与多用户

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

### 4.8 可观测性与管理功能

**实现方式：**

- **仪表盘** (`backend/app/api/dashboard.py`)：
  - 管理员专用端点，返回论文/用户/聊天数量、总 Token 使用量、预估费用、近期活动。

- **用量追踪** (`backend/app/services/usage_tracker.py`)：
  - `TokenUsage` 模型记录每次 LLM 调用的 prompt/completion/total tokens、模型、端点、费用估算。
  - `UsageTracker` 聚合每个用户和全局的统计信息。

- **通知** (`backend/app/api/notifications.py`)：
  - 摘要订阅（基于关键词的 arXiv 提醒）、系统通知（已读/未读跟踪）、轮询未读计数。

- **设置** (`backend/app/api/settings.py`)：
  - 个人资料编辑、头像上传（base64）、密码修改、API 配置展示（密钥已脱敏）、可用网络搜索提供商列表。

---

### 4.9 后台任务队列

**实现方式** (`backend/app/tasks/`)：
- `celery_app.py` —— Celery 应用配置，Redis Broker
- `paper_tasks.py` —— 异步任务：`download_paper`（从 arXiv 下载）、`parse_pdf`（提取文本）、`generate_embedding`（向量化）
- `daily_digest.py` —— 为订阅用户定时生成 arXiv 每日摘要
- **API** (`backend/app/api/tasks.py`)：提交和查询任务状态（使用 Celery `AsyncResult`）

---

### 4.10 全文加载与小组报告

**实现方式：**

- **PDF 全文加载** (`backend/app/services/report_service.py`)：
  - `ensure_full_text()` 异步从 arXiv 下载 PDF（httpx），用 pdfplumber/fitz 提取文本，缓存至数据库。
  - 在论文详情页触发后台预加载。

- **小组报告** (`backend/app/services/report_service.py`)：
  - `ReportService.generate_report()` 接收论文 ID 列表，调用 LLM 对每篇论文进行结构化分析（问题/方法/结果/优势/不足），返回 Markdown，并通过 python-docx 生成 .docx 文件。

- **飞书集成** (`backend/app/services/feishu_service.py`)：
  - 通过飞书（Lark）API 将报告写入飞书文档。

---

## 五、测试

项目包含 13 个后端测试文件和 1 个前端测试文件（位于 `backend/tests/` 和 `frontend/tests/`）：

| 测试文件 | 测试范围 |
|----------|----------|
| `test_paper_discovery_search_and_ingest.py` | 论文搜索和导入工作流 |
| `test_paper_full_text_reliability.py` | 全文加载鲁棒性 |
| `test_paper_detail_chat_parity.py` | 论文问答一致性 |
| `test_paper_reader_grounded_interaction.py` | 基于证据的论文阅读交互 |
| `test_scholarly_source_pdf_and_google_scholar.py` | 学术源可靠性 |
| `test_chat_retrieval_mode_coordination.py` | RAG/网络搜索检索协调 |
| `test_streamed_chat_empty_response_protection.py` | 空响应处理 |
| `test_web_search_reliability.py` | 网络搜索鲁棒性 |
| `test_core_workflow_stabilization.py` | 核心工作流稳定性 |
| `test_multi_user_authorization_boundaries.py` | 多用户认证边界 |
| `test_profile_identity_sync.py` | 个人资料一致性 |
| `test_research_idea_workbench.py` | 研究思路工作台流水线 |
| `test_retrieval_quality_evaluation.py` | 检索质量基准 |
| `test_writing_assistant_v2.py` | 写作助手 V2 |
| `app-layout-contract.test.mjs` | 前端布局契约测试 |

---

## 六、部署架构

系统通过 Docker Compose 编排 5 个服务：

```
┌────────────────────────────────────────────────┐
│                    Nginx                        │
│            (反向代理 + 静态资源)                  │
└──────┬──────────────────────┬──────────────────┘
       │                      │
       ▼                      ▼
┌──────────────┐    ┌──────────────────┐
│   Frontend   │    │  Backend (FastAPI) │
│  (静态页面)   │    │   (API 服务)       │
└──────────────┘    └────┬──────┬──────┘
                         │      │
                ┌────────▼──┐ ┌─▼──────────┐
                │ PostgreSQL │ │   Redis    │
                │ + pgvector │ │ (Broker +  │
                │            │ │   Cache)   │
                └────────────┘ └────┬───────┘
                                    │
                           ┌────────▼──────────┐
                           │   Celery Worker    │
                           │ (异步任务处理)      │
                           └────────────────────┘
```

- **开发环境**：使用 `docker-compose.yml`，支持热重载
- **生产环境**：使用 `docker-compose.prod.yml` 覆盖配置，启用 HTTPS、收紧安全策略

---

## 七、总结

Auto-Research-DS 是一个功能完备、面向学术研究团队的生产级平台，其核心特色包括：

1. **多源论文发现** —— 4 个学术 API + 2 种导入格式 + PDF 代理，全部去重
2. **深度混合搜索** —— BM25 + pgvector 稠密向量 + 交叉编码器重排序，自适应融合
3. **有证据支撑的思路生成** —— 创新的 7 阶段流水线：收集证据 → 映射研究缺口 → 多路径生成假设 → 六维度评审 → 可追溯的全过程产物
4. **多智能体写作流水线** —— 5 个专业智能体（选择、阅读、写作、评审、引文）通过 SSE 协调，带版本控制的差异润色和引文验证
5. **多源网络搜索** —— 4 个结构化 API 提供商 + 2 个 HTML 回退，含查询规划和去重
6. **生产级部署** —— Docker Compose 5 服务编排，支持开发和生产配置
7. **中文优先体验** —— Ant Design zh_CN、中文论文处理、NSFC 基金申请支持
