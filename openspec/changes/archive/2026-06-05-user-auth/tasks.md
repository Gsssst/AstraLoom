## 1. 后端安全模块

- [x] 1.1 实现 backend/app/core/security.py（JWT 生成/验证、密码哈希）
- [x] 1.2 实现 User ORM 模型 (backend/app/db/models/user.py)

## 2. 认证 API

- [x] 2.1 实现 backend/app/api/auth.py（register, login, refresh, me）
- [x] 2.2 实现认证中间件（get_current_user, get_optional_user）
- [x] 2.3 在 main.py 注册 auth 路由

## 3. 数据库迁移

- [x] 3.1 创建 Alembic 迁移脚本（users 表）
- [x] 3.2 运行迁移验证

## 4. 前端认证

- [x] 4.1 升级 LoginPage（完整登录表单 + API 调用）
- [x] 4.2 创建 RegisterPage（注册表单）
- [x] 4.3 升级 useAuthStore（登录/登出/Token 持久化/用户信息）
- [x] 4.4 更新 AppLayout 用户区域（显示用户名 + 退出登录）
- [x] 4.5 更新路由（注册页面 + 登录拦截）

## 5. 集成验证

- [x] 5.1 测试注册/登录/Token 刷新 API
- [x] 5.2 前端构建验证
