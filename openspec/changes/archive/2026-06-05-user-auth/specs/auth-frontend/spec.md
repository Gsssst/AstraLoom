## ADDED Requirements

### Requirement: 登录页面
前端 SHALL 提供完整的登录页面，支持用户名/邮箱 + 密码登录。

#### Scenario: 成功登录
- **WHEN** 用户输入正确的凭据并提交
- **THEN** Token 存储到 localStorage
- **AND** 页面跳转到主页

### Requirement: 注册页面
前端 SHALL 提供用户注册页面。

#### Scenario: 成功注册
- **WHEN** 用户填写注册表单并提交
- **THEN** 自动登录并跳转到主页

### Requirement: 认证状态管理
前端 SHALL 使用 Zustand 管理认证状态，页面刷新后保持登录状态。

#### Scenario: 页面刷新保持登录
- **WHEN** 用户已登录并刷新页面
- **THEN** 从 localStorage 恢复 Token 和用户信息
