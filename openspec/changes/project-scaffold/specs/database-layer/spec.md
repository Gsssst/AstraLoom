## ADDED Requirements

### Requirement: 数据库连接管理
系统 SHALL 使用 SQLAlchemy 异步引擎管理 PostgreSQL 数据库连接，连接参数通过环境变量配置。

#### Scenario: 数据库连接成功
- **WHEN** 服务启动时初始化数据库连接池
- **THEN** 连接到 PostgreSQL 数据库成功
- **AND** 连接池大小可配置（默认 20）

#### Scenario: 数据库连接失败
- **WHEN** 数据库不可达
- **THEN** 启动时记录明确错误信息
- **AND** 返回非零退出码

### Requirement: pgvector 向量扩展
数据库 SHALL 启用 pgvector 扩展，支持向量存储和相似度检索。

#### Scenario: 向量扩展已启用
- **WHEN** 数据库初始化完成后
- **THEN** `CREATE EXTENSION IF NOT EXISTS vector` 已执行
- **AND** 可以创建包含 `VECTOR(1536)` 或 `VECTOR(1024)` 类型列的表

### Requirement: Alembic 数据库迁移
系统 SHALL 使用 Alembic 管理数据库 schema 版本，支持自动生成迁移脚本。

#### Scenario: 执行数据库迁移
- **WHEN** 运行 `alembic upgrade head`
- **THEN** 所有待执行的迁移被应用到数据库
- **AND** `alembic_version` 表记录当前版本号

#### Scenario: 自动生成迁移
- **WHEN** 修改 SQLAlchemy 模型后运行 `alembic revision --autogenerate -m "description"`
- **THEN** 生成包含 schema 差异的迁移脚本

### Requirement: 基础模型
系统 SHALL 定义包含通用字段的基础 ORM 模型，供所有业务模型继承。

#### Scenario: 模型继承基础模型
- **WHEN** 创建新的 ORM 模型类
- **THEN** 自动包含 `id` (UUID), `created_at`, `updated_at` 字段
- **AND** 继承 TimestampMixin 提供时间戳
