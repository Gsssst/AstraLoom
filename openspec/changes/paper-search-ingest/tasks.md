## 1. 数据库模型和迁移

- [x] 1.1 实现 Paper ORM 模型 (backend/app/db/models/paper.py)
- [x] 1.2 实现 Category 和 PaperCategory ORM 模型
- [x] 1.3 创建 Alembic 迁移脚本（papers, categories, paper_categories 表）
- [x] 1.4 更新 backend/app/db/base.py 注册新模型

## 2. 论文检索服务

- [x] 2.1 实现 backend/app/services/paper_search.py（arXiv API 封装，使用 arxiv 库）
- [x] 2.2 实现 Semantic Scholar API 搜索（作为补充源）
- [x] 2.3 实现 LLM 推荐论文功能（对话中提取研究方向 → 搜索论文的基础框架已就绪）
- [x] 2.4 安装新依赖：arxiv Python 库 + feedparser

## 3. 论文入库管道

- [x] 3.1 实现 backend/app/services/paper_ingestion.py（元数据提取 + 去重 + 入库）
- [x] 3.2 实现去重逻辑（arXiv ID → DOI → 标题相似度 三级检查）
- [x] 3.3 集成为 Celery 异步任务（论文下载任务自动提交）

## 4. 论文 API

- [x] 4.1 实现 backend/app/api/papers.py（论文搜索、详情、分类管理 API）
- [x] 4.2 实现论文入库 API（POST /api/papers/ingest）
- [x] 4.3 在 backend/app/main.py 注册新路由

## 5. 前端论文库页面

- [x] 5.1 升级 PapersPage 为完整论文库界面（搜索框 + 列表 + 分页）
- [x] 5.2 实现论文搜索 UI（搜索框、分类筛选下拉、时间范围选择）
- [x] 5.3 实现论文详情抽屉/模态框
- [x] 5.4 实现论文分类标签展示

## 6. 集成验证

- [x] 6.1 测试 arXiv API 搜索功能 ✅ (成功检索 "Attention Is All You Need")
- [x] 6.2 测试论文入库流水线 ✅ (搜索 → 去重 → 入库)
- [x] 6.3 API 搜索和详情查询 ✅
