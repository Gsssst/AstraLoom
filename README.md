# Auto-Research-DS

自动化科研工作流系统 — 面向课题组的论文知识库管理与 AI 辅助研究平台。

## 功能概览

- **论文知识库**：自动检索、分类存储、向量语义搜索
- **科研 Pipeline**：前沿论文获取 → 总结 → Idea 生成 → 多人讨论
- **Web 界面**：课题组多人同时访问，统一部署在服务器
- **写作助手**：智能引用推荐、Related Work 自动生成、BibTeX 管理

## 技术栈

| 层次 | 技术 |
|------|------|
| 后端 | Python 3.12, FastAPI, SQLAlchemy, Alembic, Celery |
| 数据库 | PostgreSQL 16 + pgvector |
| 缓存 | Redis 7 |
| 前端 | React 18, TypeScript, Vite, Ant Design |
| LLM | DeepSeek V4 Pro (via LiteLLM) |
| 部署 | Docker Compose, Nginx |

## 快速开始

### 1. 克隆仓库

```bash
git clone <repo-url>
cd auto-Research-DS
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入你的 DeepSeek API Key
```

### 3. 启动全部服务

```bash
docker compose up -d
```

### 4. 访问

- 前端界面：http://localhost
- API 文档：http://localhost/api/docs
- 健康检查：http://localhost/api/health

### 5. 数据库迁移

```bash
docker compose exec backend alembic upgrade head
```

## 项目结构

```
auto-Research-DS/
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── api/          # API 路由
│   │   ├── core/         # 配置、中间件
│   │   ├── db/           # 数据库模型
│   │   ├── services/     # 业务逻辑
│   │   └── tasks/        # Celery 异步任务
│   └── alembic/          # 数据库迁移
├── frontend/             # React 前端
│   └── src/
│       ├── components/   # 通用组件
│       ├── pages/        # 页面
│       ├── services/     # API 请求
│       └── stores/       # 状态管理
├── nginx/                # Nginx 配置
├── docker-compose.yml    # 开发环境
└── openspec/             # 开发规范
```

## 开发

### 后端开发

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 前端开发

```bash
cd frontend
npm install
npm run dev
```

## 许可证

MIT
