## 1. 数据模型与数据库迁移

- [x] 1.1 创建 `WritingProject` 模型 (id, user_id, title, description, template_type, status, metadata_json, timestamps)
- [x] 1.2 创建 `WritingSection` 模型 (id, project_id, title, content, order, status, word_count, timestamps)
- [x] 1.3 创建 `PolishVersion` 模型 (id, section_id, original_text, polished_text, diff_json, version_number, user_actions, timestamps)
- [x] 1.4 生成 Alembic 迁移脚本并执行 `alembic upgrade head`

## 2. Pipeline 引擎核心

- [x] 2.1 创建 `app/services/writing_pipeline.py` — Pipeline 引擎类，支持阶段编排、事件队列、取消机制
- [x] 2.2 实现 Pipeline 阶段配置：轻量级 (Writer→Reviewer)、标准 (Selector→Reader→Writer→Citation)、重量级 (全部五阶段)
- [x] 2.3 实现 SSE 事件发射器：phase_start、content (token 流式)、phase_complete、error、cancelled、done
- [x] 2.4 实现 Pipeline 取消机制：`asyncio.Event` 信号 + Agent 检查点

## 3. Agent 实现

- [x] 3.1 创建 `app/services/agents/` 模块，定义 Agent 基类 (抽象 `execute()` 方法、共享 LLM 实例、日志记录)
- [x] 3.2 实现 SelectorAgent — 分析写作意图、选择检索策略、输出论文阅读计划
- [x] 3.3 实现 ReaderAgent — 深度阅读论文、提取结构化信息 (问题/方法/结果/关系)、写入工作记忆
- [x] 3.4 实现 WriterAgent — 基于工作记忆生成写作内容、支持流式 token 输出、遵循格式约束
- [x] 3.5 实现 ReviewerAgent — 审阅 Writer 输出、从逻辑/语言/结构三个维度提出修改建议
- [x] 3.6 实现 CitationAgent — 提取 Writer 输出中的引用标记、调用外部 API 验证、标记验证状态

## 4. LaTeX 感知处理器

- [x] 4.1 创建 `app/services/latex_processor.py` — LaTeX 块检测器
- [x] 4.2 实现 LaTeX 块保护：占位符替换 → LLM 处理 → 还原
- [x] 4.3 实现 `.tex` 文件导入：解析 section 结构、提取文本、关联 bib 文件
- [x] 4.4 实现 LaTeX 项目导出：渲染为 .tex + .bib 文件
- [x] 4.5 实现 LaTeX 编译检查：pdflatex + 错误报告 + 自动重试 (最多 3 次)

## 5. Diff 引擎

- [x] 5.1 创建 `app/services/diff_engine.py` — 句子级 diff
- [x] 5.2 实现 LaTeX 感知 diff：保护 LaTeX 块，排除受保护块
- [x] 5.3 实现 Diff hunks 生成：统一格式 + 位置标注 + 上下文
- [x] 5.4 实现 hunks apply/reject 逻辑

## 6. 引用验证器

- [x] 6.1 创建 `app/services/citation_verifier.py` — 多源并行验证引擎
- [x] 6.2 实现 Semantic Scholar API 查询
- [x] 6.3 实现 CrossRef API 查询
- [x] 6.4 实现 arXiv API 查询
- [x] 6.5 实现 2/3 多数投票 + Redis 24h 缓存
- [x] 6.6 实现幻觉引用模糊匹配修复建议

## 7. 智能引用推荐增强

- [x] 7.1 创建 `app/services/smart_citation_service.py`
- [x] 7.2 实现引用位置检测
- [x] 7.3 实现多源检索合并 (本地 + Semantic Scholar + arXiv)
- [x] 7.4 生成带定位提示的引用建议 (每个推荐附带"支持哪个论点"的说明)

## 8. 多智能体 Related Work 生成

- [x] 8.1 Selector 阅读策略 (已在 agents/selector_agent.py 实现)
- [x] 8.2 Reader 工作记忆 (已在 agents/reader_agent.py 实现)
- [x] 8.3 论文关系图构建 (已在 agents/reader_agent.py 实现)
- [x] 8.4 Writer 分组生成 (已在 agents/writer_agent.py 实现)

## 9. 写作项目管理 (后端)

- [x] 9.1 创建 `app/services/writing_project_service.py`
- [x] 9.2 实现模板系统 (ACL/CVPR/NeurIPS/ICML/NSFC/空白)
- [x] 9.3 实现章节管理 (增删改排序、状态流转)
- [x] 9.4 实现多格式导出 (Word/Markdown/LaTeX)
- [x] 9.5 实现项目进度统计

## 10. API 端点

- [x] 10.1 升级 `/api/writing/*` 路由 (writing_v2.py 兼容现有签名)
- [x] 10.2 新增 `/api/writing/pipeline/stream` SSE 流式端点
- [x] 10.3 新增 `/api/writing/projects` CRUD 端点
- [x] 10.4 新增 `/api/writing/projects/{id}/sections` 章节管理
- [x] 10.5 新增 `/api/writing/projects/{id}/export` 多格式导出
- [x] 10.6 新增 `/api/writing/polish/diff` Diff 润色端点
- [x] 10.7 新增 `/api/writing/citations/verify` 引用验证
- [x] 10.8 新增 `/api/writing/latex/import` LaTeX 导入

## 11. 前端组件

- [x] 11.1 创建 `DiffViewer` 组件
- [x] 11.2 创建 `PipelineProgress` 组件
- [x] 11.3 创建 `WritingProjectPanel` 组件
- [x] 11.4 创建 `SectionEditor` 组件
- [x] 11.5 创建 `CitationVerifyBadge` 组件
- [x] 11.6 重构 `WritingPage.tsx`：集成新组件

## 12. 集成与测试

- [x] 12.1 Pipeline 引擎单元测试
- [x] 12.2 Agent 单元测试
- [x] 12.3 LaTeX 处理器测试
- [x] 12.4 Diff 引擎测试
- [x] 12.5 引用验证器测试
- [x] 12.6 后端集成测试
- [x] 12.7 前端集成测试 (组件可正确导入)
