## Context

系统当前所有 API 都是公开的，但后续功能（个人论文库、对话历史、研究项目）需要用户隔离。需要建立基本的用户认证和授权机制。

## Goals / Non-Goals

**Goals:**
- 用户注册（用户名 + 邮箱 + 密码）
- 用户登录（返回 JWT access_token + refresh_token）
- Token 刷新
- 认证中间件（HTTP Bearer Token）
- 角色基础授权（user / admin）
- 前端登录/注册页面 + 状态持久化

**Non-Goals:**
- 不做 OAuth/SSO（后续可扩展）
- 不做邮箱验证（后续可加）
- 不做复杂的 RBAC（后续可扩展）

## Decisions

### 1. 认证方案：JWT (access + refresh)

- access_token: 30 分钟有效期
- refresh_token: 7 天有效期
- 签名算法：HS256（对称加密，使用 SECRET_KEY）

### 2. 密码哈希：bcrypt (passlib)

- passlib 的 bcrypt 实现
- cost factor = 12

### 3. User 模型设计

```python
class User(BaseModel):
    username: str (unique, indexed)
    email: str (unique, indexed)
    hashed_password: str
    role: str (user / admin, default=user)
    is_active: bool (default=True)
```

### 4. Token 存储

- 前端：access_token 存 localStorage，refresh_token 存 localStorage
- 后端：无状态，每次请求解析 JWT

## Risks / Trade-offs

- JWT 无法主动撤销 → 使用短 access_token + 长 refresh_token 平衡安全性和用户体验
- localStorage 有 XSS 风险 → 后续可用 httpOnly cookie 方案升级
