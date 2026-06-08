# AstraLoom

## 项目概述

AstraLoom 智能科研工作台（AstraLoom），部署在 Linux 服务器上，为课题组提供：
- 论文检索与持久化分类知识库
- 基于大模型的科研 Idea 生成与讨论
- 论文写作辅助（引用推荐、Related Work 生成等）
- Web 前端界面供课题组多人访问

## 技术栈

| 层次 | 技术 |
|------|------|
| 后端 | Python 3.12+, FastAPI, SQLAlchemy, Alembic |
| 数据库 | PostgreSQL 16 + pgvector (向量检索) |
| 缓存/队列 | Redis, Celery/Arq |
| 前端 | React 18+, TypeScript, Vite, Ant Design |
| LLM | DeepSeek V4 Pro API (via LiteLLM 统一接口) |
| 论文检索 | arXiv API, Semantic Scholar API |
| 部署 | Docker Compose, Nginx |

## 语言支持

- 系统界面和输出默认使用中文
- 论文元数据保留原文（英文为主）
- 论文总结支持中英文输出

## 目标用户

课题组内多位研究人员，通过各自的电脑浏览器访问部署在服务器上的系统。

## 开发方法

采用 OpenSpec 规范驱动开发（SDD），每个功能模块作为一个独立的 change proposal 进行。
