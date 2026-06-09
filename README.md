# AstraLoom

> 中文 | [English](#english)

AstraLoom 是面向课题组和实验室的自部署 AI 科研工作台。它不是一个面向全网用户的公共 SaaS 网站，而是希望每个实验室都可以部署一套属于自己的系统，用来管理本组论文库、沉淀研究方向、辅助 idea 生成、评估 proposal、推进 LaTeX 写作和实验规划。

## 项目定位

- **实验室自部署**：每个课题组独立部署，论文、笔记、API Key、研究方向和讨论记录都保存在自己的服务器或工作站中。
- **组内论文管理**：统一导入、检索、标记、分类和阅读论文，支持“我的论文”、重点/感兴趣标记、组会报告等工作流。
- **Auto Research 工作流**：从论文证据和 Gap Map 出发生成 proposal，并用新颖性、证据支撑、工具适配、实验质量等维度排序。
- **写作与实验衔接**：把 proposal、证据卡、BibTeX、figures 清单和 LaTeX 章节写作连接起来，减少从 idea 到论文草稿的断层。
- **可配置模型接口**：支持 DeepSeek 和 OpenAI Chat Completions / Responses 兼容端点，便于不同实验室接入自己的模型服务。

## 主要功能

- **论文库**：论文导入、语义检索、分类、标签、重要性标记、PDF 阅读和划词问答。
- **研究方向工作台**：Evidence Map、Gap Map、候选池、proposal 排序、idea 讨论和迭代。
- **算法评审信号**：新颖性矩阵、证据支撑矩阵、实验质量评估、工具箱适配和多样性选择。
- **工具箱**：沉淀论文中出现的方法、数据集、指标、协议和工具，并在 idea 生成时选择使用。
- **写作助手**：按章节写 LaTeX，支持编译预览、BibTeX 面板、引用建议和 AI 辅助写作。
- **项目空间**：把论文、研究方向、写作项目、反馈 issue 和 AI 助手放在同一个组内工作区。

## 技术栈

| 层次 | 技术 |
| --- | --- |
| 后端 | Python 3.12, FastAPI, SQLAlchemy, Alembic, Celery |
| 数据库 | PostgreSQL 16, pgvector |
| 缓存/任务 | Redis 7, Celery Beat |
| 前端 | React 18, TypeScript, Vite, Ant Design |
| LLM | DeepSeek / OpenAI-compatible endpoints via LiteLLM |
| 部署 | Docker Compose, Nginx |
| 研发流程 | OpenSpec |

## 快速开始

### 1. 克隆仓库

```bash
git clone <repo-url>
cd AstraLoom
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，至少配置数据库、密钥和 LLM API。不要把 `.env` 上传到 GitHub。

### 3. 启动服务

```bash
docker compose up -d
```

默认访问：

- 前端界面：http://localhost
- API 文档：http://localhost/api/docs
- 健康检查：http://localhost/api/health
- 数据库迁移检查：http://localhost/api/health/db

### 4. 数据库迁移

容器启动时默认会执行 Alembic 迁移。开发或排障时可以手动执行：

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend alembic current
curl http://127.0.0.1:8000/api/health/db
```

## 模型配置

DeepSeek 示例：

```bash
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your-deepseek-api-key
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-pro
```

OpenAI 兼容端点示例：

```bash
LLM_PROVIDER=openai-compatible
OPENAI_COMPATIBLE_API_KEY=sk-your-compatible-api-key
OPENAI_COMPATIBLE_API_BASE=https://your-compatible-endpoint/v1
OPENAI_COMPATIBLE_MODEL=gpt-5.5
```

如果端点支持 OpenAI Responses API，也可以在设置页中启用对应模型能力。不同实验室可以根据自己的预算、合规要求和模型服务选择配置。

## 项目结构

```text
AstraLoom/
├── backend/              # FastAPI 后端、数据库模型、服务和 Celery 任务
├── frontend/             # React 前端
├── nginx/                # Nginx 配置
├── openspec/             # OpenSpec 需求与变更记录
├── docker-compose.yml    # 本地/实验室部署编排
├── docker-compose.prod.yml
├── introduction.md       # 项目介绍
├── user-manual.md        # 用户手册
└── README.md
```

## GitHub 上传建议

应该上传：

- `backend/`
- `frontend/`
- `nginx/`
- `openspec/`
- `README.md`
- `introduction.md`
- `user-manual.md`
- `.gitignore`
- `.env.example`
- `docker-compose.yml`
- `docker-compose.prod.yml`

不要上传：

- `.env`、`.env.local`、`.env.production`
- API Key、数据库密码、JWT 密钥等任何真实密钥
- `node_modules/`、`dist/`、`.vite/`
- `.venv/`、`venv/`、`__pycache__/`
- `.pytest_cache/`
- `.DS_Store`
- `.idea/`、`.vscode/`
- `uploads/`、`logs/`
- `backend/celerybeat-schedule`
- 任何真实论文 PDF、未公开数据集、组内私有笔记或用户上传文件

当前仓库已经包含 `.gitignore` 和 `.env.example`。在 GitHub 创建空仓库时，不要勾选自动创建 README、`.gitignore` 或 license，避免和本地历史冲突。

## 开发

后端：

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

前端：

```bash
cd frontend
npm install
npm run dev
```

构建：

```bash
cd frontend
npm run build
```

测试示例：

```bash
docker compose exec -T backend env PYTHONPATH=/app pytest tests/test_research_idea_workbench.py -q
node --test frontend/tests/research-toolbox-contract.test.mjs
openspec validate --specs --strict
```

## 部署建议

- 建议先在课题组内网或实验室服务器部署。
- 对外暴露服务前，应配置 HTTPS、强密码、备份策略和访问控制。
- 论文 PDF、用户上传文件和数据库备份不要提交到 GitHub。
- 多人使用时建议为每个成员创建独立账号，避免共享管理员账号。

## 许可证

当前仓库尚未添加 license 文件。若后续决定开源，建议先确认课题组/单位对代码、模型调用和论文数据的合规要求，再选择 MIT、Apache-2.0 或其他协议。

---

## English

AstraLoom is a self-hosted AI research workspace for research groups and academic labs. It is not designed as a centralized public SaaS product. Instead, each lab can deploy its own instance, keep its papers, notes, API keys, research directions, and discussions under local control, and use the system as an internal research infrastructure.

## Positioning

- **Self-hosted for labs**: Each lab owns its deployment, data, model keys, and research records.
- **Lab paper management**: Import, search, classify, tag, read, and discuss papers in one shared workspace.
- **Auto Research workflow**: Generate and rank proposals from paper evidence and Gap Maps using novelty, evidence grounding, toolbox fit, and experiment quality signals.
- **Writing and experiment bridge**: Connect proposals, evidence cards, BibTeX, figure lists, LaTeX sections, and experiment plans.
- **Configurable model endpoints**: Supports DeepSeek and OpenAI Chat Completions / Responses-compatible endpoints through LiteLLM.

## Key Features

- **Paper library**: Paper ingestion, semantic search, collections, tags, importance markers, PDF reading, and selection-based AI Q&A.
- **Research idea workbench**: Evidence Map, Gap Map, candidate pool, proposal ranking, idea discussion, and iterative refinement.
- **Algorithmic review signals**: Novelty matrix, evidence grounding matrix, experiment quality evaluation, toolbox fit, and diversity-aware selection.
- **Toolbox**: Store methods, datasets, metrics, protocols, and tools found in papers, then reuse them during idea generation.
- **Writing assistant**: Section-based LaTeX writing, compile preview, BibTeX panel, citation suggestions, and AI writing assistance.
- **Project spaces**: Combine papers, research projects, writing drafts, feedback issues, and an AI assistant in one lab workspace.

## Quick Start

```bash
git clone <repo-url>
cd AstraLoom
cp .env.example .env
docker compose up -d
```

Then open:

- Web app: http://localhost
- API docs: http://localhost/api/docs
- Health check: http://localhost/api/health

Do not commit `.env` or any real API keys to GitHub.

## What To Upload To GitHub

Upload source code, configuration templates, OpenSpec documents, and public documentation:

- `backend/`, `frontend/`, `nginx/`, `openspec/`
- `README.md`, `introduction.md`, `user-manual.md`
- `.gitignore`, `.env.example`
- `docker-compose.yml`, `docker-compose.prod.yml`

Do not upload secrets, runtime files, generated folders, private papers, uploaded PDFs, local IDE files, logs, caches, or database backups.

## License

No license file has been added yet. Before making the repository public or open source, confirm your lab or institution's policy and choose an appropriate license.
