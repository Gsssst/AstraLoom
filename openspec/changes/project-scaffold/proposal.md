## Why

Auto-Research-DS 是一个面向课题组的多用户科研工作流系统，需要在此基础上统一的后端服务、数据库、前端框架和容器化部署方案。目前项目目录为空，需要搭建完整的项目基础设施，为后续所有功能模块（论文知识库、RAG 引擎、自动化科研 Pipeline、前端界面、写作助手）提供运行底座。

## What Changes

- 初始化 Python FastAPI 后端项目结构，包含路由、中间件、配置管理
- 初始化 React + TypeScript + Vite 前端项目结构
- 配置 Docker Compose 开发/生产环境，包含 PostgreSQL+pgvector、Redis、Nginx
- 建立 Alembic 数据库迁移框架
- 引入 LiteLLM 作为 LLM 统一调用接口
- 配置项目环境变量管理（.env）
- 建立 Celery 任务队列（用于异步论文下载、PDF 解析等）
- 统一的日志和异常处理机制

## Capabilities

### New Capabilities

- `backend-api`: FastAPI 后端 API 服务，提供 RESTful 接口和 WebSocket 支持
- `database-layer`: PostgreSQL + pgvector 数据库层，含 Alembic 迁移管理
- `frontend-app`: React + TypeScript 前端应用，Vite 构建
- `deployment`: Docker Compose 部署方案，含 Nginx、Redis、Celery Worker

### Modified Capabilities

<!-- 首次建立，无已有规范需要修改 -->

## Impact

- 项目根目录将从空目录变为完整的 monorepo 结构
- 后端依赖：fastapi, uvicorn, sqlalchemy, asyncpg, alembic, pgvector, celery, litellm, pydantic
- 前端依赖：react, typescript, vite, antd, zustand, react-router, axios
- 基础设施依赖：Docker, Docker Compose, PostgreSQL 16, Redis 7, Nginx
