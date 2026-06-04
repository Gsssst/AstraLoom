## ADDED Requirements

### Requirement: User 模型
系统 SHALL 定义 User ORM 模型，包含用户名、邮箱、加密密码和角色字段。

#### Scenario: 创建用户
- **WHEN** 新用户注册
- **THEN** users 表新增记录，密码使用 bcrypt 加密存储
- **AND** username 和 email 具有唯一约束

### Requirement: Alembic 迁移
系统 SHALL 创建 users 表的数据库迁移。

#### Scenario: 执行迁移
- **WHEN** 运行 `alembic upgrade head`
- **THEN** users 表被创建，包含所有必要索引
