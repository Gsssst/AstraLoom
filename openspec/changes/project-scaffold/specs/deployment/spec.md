## ADDED Requirements

### Requirement: Docker Compose 开发环境
系统 SHALL 提供 `docker-compose.yml` 文件，定义所有服务并支持一键启动开发环境。

#### Scenario: 启动全部服务
- **WHEN** 在项目根目录执行 `docker compose up -d`
- **THEN** 以下服务全部启动：backend, frontend, postgres, redis, celery-worker, nginx
- **AND** 各服务之间网络互通

#### Scenario: 代码热重载
- **WHEN** 修改后端 Python 代码
- **THEN** backend 服务自动重载（通过 volume mount + uvicorn --reload）
- **WHEN** 修改前端代码
- **THEN** frontend 服务通过 Vite HMR 自动更新

### Requirement: Nginx 反向代理
Nginx SHALL 作为统一入口，将请求代理到后端 API 和前端静态文件。

#### Scenario: API 请求代理
- **WHEN** 浏览器访问 `http://localhost/api/*`
- **THEN** Nginx 将请求代理到 backend 服务
- **AND** 正确传递请求头和 WebSocket 升级

#### Scenario: 前端静态文件
- **WHEN** 浏览器访问 `http://localhost/`
- **THEN** Nginx 提供前端静态文件和 SPA fallback（所有非 API 路径返回 index.html）

### Requirement: 环境变量管理
系统 SHALL 通过 `.env` 文件和 `docker-compose` 的 `env_file` 指令管理环境变量，并提供 `.env.example` 作为模板。

#### Scenario: 配置环境变量
- **WHEN** 开发者复制 `.env.example` 为 `.env` 并填入实际值
- **THEN** Docker Compose 自动加载环境变量
- **AND** 各服务获取对应的配置值

### Requirement: 数据持久化
数据库和文件上传 SHALL 使用 Docker 命名卷进行持久化，服务重启不丢失数据。

#### Scenario: 数据持久化
- **WHEN** 执行 `docker compose down` 后重新 `docker compose up -d`
- **THEN** PostgreSQL 数据完整保留
- **AND** 上传的文件完整保留

### Requirement: 生产环境覆盖
系统 SHALL 提供 `docker-compose.prod.yml` 覆盖文件，配置生产环境的安全参数。

#### Scenario: 生产部署
- **WHEN** 使用 `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`
- **THEN** 使用生产级配置：关闭 DEBUG 模式、使用非默认端口、限制资源
