## ADDED Requirements

### Requirement: API 服务启动
后端服务 SHALL 使用 Uvicorn 作为 ASGI 服务器，在配置的端口上监听 HTTP 请求。

#### Scenario: 服务启动成功
- **WHEN** 执行 `docker compose up backend`
- **THEN** 服务在 `http://localhost:8000` 上响应请求
- **AND** `/docs` 端点提供交互式 API 文档

#### Scenario: 健康检查
- **WHEN** 发送 GET 请求到 `/api/health`
- **THEN** 返回 `{"status": "ok"}` JSON 响应

### Requirement: 配置管理
系统 SHALL 通过环境变量管理所有配置项，使用 Pydantic Settings 进行验证。

#### Scenario: 加载环境变量
- **WHEN** 服务启动时
- **THEN** 从 `.env` 文件加载配置
- **AND** 缺少必需配置项时抛出明确错误

### Requirement: LLM 接口封装
系统 SHALL 通过 LiteLLM 统一封装 LLM 调用，默认使用 DeepSeek V4 Pro。

#### Scenario: 调用 LLM 完成对话
- **WHEN** 调用 `POST /api/chat/completions` 并传入 messages
- **THEN** 通过 LiteLLM 调用 DeepSeek API 并返回流式/非流式响应
- **AND** 支持配置 `DEEPSEEK_API_KEY` 和 `DEEPSEEK_API_BASE`

### Requirement: 异常处理中间件
系统 SHALL 提供全局异常处理，将未捕获异常转换为统一的 JSON 错误响应。

#### Scenario: 未捕获异常
- **WHEN** API 处理过程中发生未预期错误
- **THEN** 返回 `{"error": {...}, "status": 500}` JSON 响应
- **AND** 错误详情记录到日志

### Requirement: CORS 支持
系统 SHALL 配置 CORS 中间件，允许前端跨域访问。

#### Scenario: 跨域请求
- **WHEN** 前端从不同端口发起 API 请求
- **THEN** 响应包含正确的 CORS 头部
- **AND** 允许配置 `CORS_ORIGINS` 环境变量

### Requirement: 异步任务队列
系统 SHALL 集成 Celery 异步任务队列，用于处理论文下载、PDF 解析等耗时操作。

#### Scenario: 提交异步任务
- **WHEN** 调用 `POST /api/tasks/{task_name}`
- **THEN** 任务被提交到 Celery Worker
- **AND** 返回 `task_id` 用于追踪任务状态
