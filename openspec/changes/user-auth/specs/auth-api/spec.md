## ADDED Requirements

### Requirement: 用户注册
系统 SHALL 提供用户注册 API。

#### Scenario: 成功注册
- **WHEN** 发送 POST /api/auth/register 含 username、email、password
- **THEN** 创建新用户并返回 access_token 和 refresh_token
- **AND** 密码使用 bcrypt 加密

#### Scenario: 用户名已存在
- **WHEN** 注册时 username 已被占用
- **THEN** 返回 409 错误

### Requirement: 用户登录
系统 SHALL 提供用户登录 API。

#### Scenario: 成功登录
- **WHEN** 发送 POST /api/auth/login 含正确的 username 和 password
- **THEN** 返回 access_token (30min) 和 refresh_token (7天)

#### Scenario: 密码错误
- **WHEN** 登录时密码不正确
- **THEN** 返回 401 错误

### Requirement: Token 刷新
系统 SHALL 提供 Token 刷新 API。

#### Scenario: 刷新 Token
- **WHEN** 发送 POST /api/auth/refresh 含有效的 refresh_token
- **THEN** 返回新的 access_token 和 refresh_token
