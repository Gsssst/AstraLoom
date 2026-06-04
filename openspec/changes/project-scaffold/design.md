## Context

Auto-Research-DS 需要从零开始搭建完整的项目基础设施。系统采用前后端分离的 monorepo 架构，通过 Docker Compose 在 Linux 服务器上一键部署。后端使用 Python FastAPI，前端使用 React + TypeScript，数据库使用 PostgreSQL + pgvector 插件以支持向量检索。

## Goals / Non-Goals

**Goals:**
- 建立可运行的最小骨架（后端能响应 API 请求，前端能展示页面）
- 配置 Docker Compose 开发环境，支持热重载
- 数据库 schema 管理框架就绪（Alembic）
- LLM 调用接口统一封装（LiteLLM）
- 异步任务队列就绪（Celery + Redis）

**Non-Goals:**
- 不实现具体的业务 API（论文检索、对话等留给后续 change）
- 不实现用户认证逻辑（留给 `user-auth` change）
- 不实现前端页面具体内容（仅搭建框架）

## Decisions

### 1. 项目目录结构：Monorepo

```
auto-Research-DS/
├── backend/                  # FastAPI 后端
│   ├── app/
│   │   ├── api/              # API 路由
│   │   ├── core/             # 配置、安全
│   │   ├── db/               # 数据库模型、session
│   │   ├── services/         # 业务逻辑
│   │   ├── tasks/            # Celery 任务
│   │   └── main.py           # 应用入口
│   ├── alembic/              # 数据库迁移
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                 # React 前端
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/         # API 调用
│   │   ├── stores/           # Zustand 状态
│   │   └── App.tsx
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml        # 开发环境
├── docker-compose.prod.yml   # 生产环境
├── nginx/                    # Nginx 配置
├── .env.example              # 环境变量模板
└── openspec/                 # 规范文件
```

**选择原因**：前后端代码在同一个仓库便于版本管理和 CI/CD，但通过 Docker Compose 各自独立构建和运行。

### 2. 后端框架：FastAPI + asyncpg

**选择原因**：
- FastAPI 原生支持异步，适合 I/O 密集的 LLM API 调用
- Pydantic v2 提供强大的数据验证
- asyncpg 是最高性能的 PostgreSQL 异步驱动
- 自动生成 OpenAPI 文档，方便前端对接

**被排除的选项**：
- Django + DRF：过于重量级，ORM 异步支持较弱
- Flask：缺少原生异步支持和自动文档生成

### 3. 前端框架：React 18 + Vite + Ant Design

**选择原因**：
- Vite 构建速度远快于 CRA/Webpack
- Ant Design 提供丰富的中文友好的企业级 UI 组件
- Zustand 比 Redux 更简洁，适合中小型项目
- TypeScript 提升代码质量和开发体验

### 4. LLM 接入：LiteLLM 统一接口

**选择原因**：
- 支持 100+ LLM 提供商统一调用
- 后续如果需要切换到 Claude 或其他模型，只需改配置
- 内置重试、回退、负载均衡

### 5. 部署方式：Docker Compose

**选择原因**：
- 一键启动全部服务，环境一致
- 开发环境通过 volume mount 支持热重载
- 生产环境通过 docker-compose.prod.yml 覆盖关键配置
- 不需要 Kubernetes 的复杂度

## Risks / Trade-offs

- **LiteLLM 依赖风险**：DeepSeek API 可能与 OpenAI 格式不完全兼容 → 使用 LiteLLM 的 DeepSeek provider 或直接使用 openai 兼容模式
- **pgvector 版本**：确保 pgvector 在 PostgreSQL 16 上可用 → Docker 镜像使用 `pgvector/pgvector:pg16`
- **开发/生产差异**：配置文件分离（.env.development / .env.production），docker-compose 覆盖机制

## Migration Plan

1. 本地开发：`docker compose up -d` 启动全部服务
2. 生产部署：`docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`
3. 数据库迁移：`docker compose exec backend alembic upgrade head`
4. 回滚：Docker Compose 服务回滚到上一版本镜像

## Open Questions

- 是否需要配置 GPU passthrough（如果后续要本地跑 embedding 模型）？初期暂不需要
- 文件存储（论文 PDF）使用本地卷还是 MinIO/S3？初期使用本地卷，后续可迁移到 MinIO
