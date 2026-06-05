## Why

课题组多人使用同一系统，需要用户认证和权限管理来保护数据安全，确保每个用户的论文库、对话记录和研究项目相互隔离。这是后续所有需要用户上下文功能的基础。

## What Changes

- 创建 User ORM 模型（用户名、邮箱、加密密码、角色）
- 实现用户注册和登录 API（JWT Token）
- 实现认证中间件（保护 API 路由，可选）
- 实现 Token 刷新机制
- 前端登录/注册页面
- 前端认证状态管理（Zustand + localStorage Token 持久化）
- 用户管理 API（仅管理员）

## Capabilities

### New Capabilities

- `user-model`: User ORM 模型和 Alembic 迁移
- `auth-api`: 注册、登录、Token 刷新、用户管理 API
- `auth-middleware`: JWT 认证中间件，保护需要登录的 API 路由
- `auth-frontend`: 登录/注册页面，认证状态管理

### Modified Capabilities

<!-- 无已有规范需修改 -->

## Impact

- 新增依赖：python-jose (JWT), passlib (密码哈希) — 已在 requirements.txt 中
- 新增表：users
- 新增 Alembic 迁移
- 新增文件：backend/app/db/models/user.py, backend/app/api/auth.py, backend/app/core/security.py
- 修改文件：backend/app/main.py (注册 auth 路由)
- 前端新增：LoginPage 完整实现, RegisterPage, useAuthStore 增强
