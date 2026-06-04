## ADDED Requirements

### Requirement: JWT 认证中间件
系统 SHALL 提供 FastAPI 依赖注入函数，从请求头中解析 JWT Bearer Token。

#### Scenario: 有效 Token
- **WHEN** 请求携带有效的 Bearer Token
- **THEN** 注入当前用户对象到路由处理函数

#### Scenario: 无效 Token
- **WHEN** 请求携带过期或伪造的 Token
- **THEN** 返回 401 Unauthorized

#### Scenario: 缺少 Token
- **WHEN** 请求未携带 Authorization 头部
- **THEN** 返回 401 Unauthorized

### Requirement: 可选认证
系统 SHALL 支持可选认证（get_optional_user），Token 不存在时不报错，user 为 None。

#### Scenario: 可选认证
- **WHEN** 请求未携带 Token 访问可选认证接口
- **THEN** 正常处理请求，user 参数为 None
