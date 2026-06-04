## 1. 项目根目录配置

- [x] 1.1 创建 .env.example 环境变量模板（数据库连接、DeepSeek API、密钥等）
- [x] 1.2 创建 .gitignore（排除 node_modules, __pycache__, .env, dist 等）
- [x] 1.3 创建 README.md（项目说明和快速开始指南）

## 2. 后端项目骨架 (backend/)

- [x] 2.1 创建 backend/ 目录结构和 requirements.txt（fastapi, uvicorn, sqlalchemy, asyncpg, alembic, pgvector, celery, redis, litellm, pydantic-settings）
- [x] 2.2 实现 backend/app/core/config.py（Pydantic Settings 配置管理）
- [x] 2.3 实现 backend/app/core/exceptions.py 和异常处理中间件
- [x] 2.4 实现 backend/app/main.py（FastAPI 应用入口，CORS 配置，健康检查端点）
- [x] 2.5 实现 backend/Dockerfile（Python 3.12 基础镜像，pip 安装依赖，uvicorn 启动）

## 3. 数据库层 (backend/app/db/)

- [x] 3.1 实现 backend/app/db/base.py（基础 ORM 模型含 UUID 主键和时间戳）
- [x] 3.2 实现 backend/app/db/session.py（异步 SQLAlchemy session 管理）
- [x] 3.3 初始化 Alembic 配置并创建初始迁移（确保 pgvector 扩展启用）
- [x] 3.4 创建 backend/app/db/init_db.py（数据库初始化脚本，启动时自动执行）

## 4. LLM 接口封装 (backend/app/services/)

- [x] 4.1 实现 backend/app/services/llm.py（LiteLLM 封装，支持 DeepSeek V4 Pro）
- [x] 4.2 实现 backend/app/api/chat.py（POST /api/chat/completions 端点，支持流式响应）

## 5. Celery 任务队列配置

- [x] 5.1 实现 backend/app/tasks/celery_app.py（Celery 应用配置）
- [x] 5.2 实现 backend/app/api/tasks.py（任务提交和状态查询 API）

## 6. 前端项目骨架 (frontend/)

- [x] 6.1 使用 Vite 脚手架创建 React + TypeScript 项目
- [x] 6.2 安装依赖：antd, zustand, react-router-dom, axios
- [x] 6.3 配置 Vite 代理（开发时将 /api 代理到 backend 服务）
- [x] 6.4 实现 frontend/src/services/api.ts（Axios 实例，统一请求/响应拦截）
- [x] 6.5 实现 frontend/src/stores/（Zustand 状态管理基础）
- [x] 6.6 实现基础布局组件（侧边栏导航 + 内容区域）
- [x] 6.7 实现路由配置（首页、占位页面）
- [x] 6.8 实现 frontend/Dockerfile（多阶段构建，Nginx 提供静态文件）

## 7. Docker Compose 部署

- [x] 7.1 创建 docker-compose.yml（postgres+pgvector, redis, backend, frontend, celery-worker, nginx）
- [x] 7.2 创建 docker-compose.prod.yml（生产环境覆盖：关闭 DEBUG、HTTPS 端口、资源限制）
- [x] 7.3 创建 nginx/nginx.conf（反向代理配置，API 代理 + 前端静态文件 + WebSocket 支持）
- [ ] 7.4 验证：本地执行 `docker compose up -d` 确认全部服务正常启动（需在目标 Linux 服务器上执行，需先配置 .env 文件）
