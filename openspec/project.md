# AstraLoom

## 项目概述

AstraLoom 是面向课题组和实验室的自部署 AI 科研工作台。它帮助实验室在自己的服务器或内网环境中管理论文库、沉淀研究工具、生成和评审 research idea、推进 LaTeX 写作、组织项目空间，并通过 AI 辅助阅读、讨论和写作。

项目不是面向全网统一运营的公共 SaaS；默认假设每个实验室部署自己的实例，并自行控制论文、上传文件、模型 API Key、研究笔记和数据库备份。

## 目标用户

- 课题组导师和学生。
- 需要共享论文库、研究方向和写作项目的实验室。
- 希望把论文证据、工具箱、proposal、实验计划和写作流程连接起来的科研团队。

## 核心模块

- 论文库：多源检索、导入、分类、重点/有趣标记、个人阅读状态、PDF 阅读、划词问答、组会报告。
- 工具箱：沉淀算法、方法、数据集、指标、协议和工具，并关联来源论文证据。
- 研究方向：Evidence Map、Gap Map、候选 idea、proposal 评审、工具适配、讨论演进、实验计划和代码项目。
- 写作助手：章节级 LaTeX 编辑、单栏/双栏/模板预览、BibTeX 面板、figures 面板、AI 章节辅助写作。
- 项目空间：绑定论文、研究方向、写作项目、成员、活动记录和反馈 issue。
- AI 对话：模型切换、RAG、网络搜索、文件上传、reasoning summary、Markdown 渲染。
- 行动中心与设置：下一步建议、用量统计、模型配置展示、语言切换、论文推送和维护入口。

## 技术栈

| 层次 | 技术 |
| --- | --- |
| 后端 | Python 3.12, FastAPI, SQLAlchemy 2, Alembic |
| 数据库 | PostgreSQL 16 + pgvector |
| 缓存/队列 | Redis, Celery worker/beat |
| 前端 | React 19, TypeScript, Vite 8, Ant Design 6 |
| LLM | LiteLLM, DeepSeek, OpenAI-compatible API, optional Responses API reasoning |
| 检索 | BM25, pgvector dense retrieval, reranking, paper chunk retrieval |
| 论文来源 | arXiv, Semantic Scholar, OpenAlex, Google Scholar/SerpApi, BibTeX, Zotero CSV |
| 部署 | Docker Compose, Nginx |

## 语言支持

- 全局导航、系统控件和 Ant Design 组件支持中文/英文切换。
- 业务页面文案当前以中文为主，英文翻译会逐步迁移。
- 论文元数据保留原始语言。
- 写作和报告生成支持按请求使用中文或英文。

## 开发方法

采用 OpenSpec 规范驱动开发。新增功能、重要算法调整和用户可见行为变化都应先建立 change，完成实现和验证后归档，并同步主规格。

开发时优先保持功能聚焦，避免继续堆叠无关模块。当前阶段更重视检索、生成、评审、写作和长任务稳定性的算法质量提升。

协作开发约定：

- 所有开发工作必须基于 OpenSpec：先确认或创建对应 change，再进入实现。
- 新功能开发前，先检索 GitHub 上类似项目或实现，学习可复用的产品和工程方案后再编码。
- 每次完成更新后，使用 Git 提交相关改动，并保持提交范围聚焦。
- 当进入“罗列接下来开发计划”的工作模式时，每次对话后都同步说明哪些计划已完成、哪些仍需迭代。

## 数据边界

代码、OpenSpec、README、用户手册、测试和示例配置可以进入 Git 仓库。`.env`、真实 API Key、论文 PDF、上传文件、私有笔记、日志、数据库数据和备份不应提交到 Git。
