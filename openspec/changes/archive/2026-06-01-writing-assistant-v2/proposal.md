## Why

当前写作助手的 8 个功能全部采用"RAG 检索 + 单次 LLM Prompt → 输出"的简单模式，缺乏多阶段协作、引用验证、迭代润色、LaTeX 感知和项目管理能力。借鉴 GPT Academic (70k+ Stars)、ScholarCopilot (COLM 2025)、OpenDraft (19 Agent Pipeline)、TexGuardian、STORM 等优秀开源项目，需要将写作助手从"一次性 Prompt 工具"升级为"多智能体协作的学术写作工作站"。

## What Changes

### 架构升级
- **BREAKING**: 写作服务从单次 Prompt 模式升级为多智能体 Pipeline 架构
- 新增 `WritingPipeline` 引擎，协调 Selector → Reader → Writer → Reviewer → Citation 五个智能体协作
- 所有写作 API 支持流式输出，实时展示各阶段进度

### 新功能
- **智能引用推荐增强**: 上下文感知的引用定位，不仅推荐论文还推荐插入位置；多源检索（本地知识库 + Semantic Scholar + arXiv）
- **Diff 视图润色**: 润色结果以 unified diff 展示，用户可逐条接受/拒绝修改；支持多轮迭代润色
- **引用验证**: 对 AI 生成的引用交叉验证 Semantic Scholar + CrossRef + arXiv，标记验证状态，检测幻觉引用
- **LaTeX 感知处理**: 润色/翻译时自动保留 LaTeX 命令、公式、引用、图表环境；支持 LaTeX 项目导入导出
- **写作项目管理**: 论文章节管理、进度追踪、多格式导出（PDF/Word/LaTeX/Markdown）、写作模板
- **多智能体 Related Work**: Selector-Reader-Writer 三智能体协作，图感知论文关系，全文深度阅读

### 功能增强
- 文本润色增加 diff 展示和迭代修改能力
- 文献综述增加论文关系图、研究趋势时间线
- 申请书助手增加 NSFC 评审标准对照、多轮修改跟踪

## Capabilities

### New Capabilities

- `writing-pipeline`: 多智能体写作 Pipeline 引擎，协调 Selector/Reader/Writer/Reviewer/Citation 五个 Agent 协作完成写作任务
- `smart-citation-recommend`: 上下文感知的智能引用推荐，分析写作内容自动判断引用位置，多源检索并生成带定位的引用建议
- `diff-view-polish`: Diff 视图润色系统，展示修改前后对比（unified diff），支持逐条接受/拒绝，多轮迭代润色和版本历史
- `citation-verify`: 引用真实性验证，交叉核验 Semantic Scholar + CrossRef + arXiv，标记验证状态（已验证/未找到/疑似幻觉），自动修复建议
- `latex-aware-processor`: LaTeX 感知处理器，润色/翻译时自动保留命令/公式/引用/图表环境，支持 LaTeX 项目导入导出和编译校验
- `writing-project-manager`: 写作项目管理，论文章节组织、进度追踪、模板管理（ACL/CVPR/NeurIPS/NSFC）、多格式导出
- `multi-agent-related-work`: 多智能体 Related Work 生成，Selector 选择阅读策略 → Reader 深度提取信息 → Writer 生成段落，支持论文关系图

### Modified Capabilities

- `writing-api`: 所有现有写作 API（/writing/*）升级为使用 Pipeline 引擎，增加流式输出和进度回调

## Impact

- **后端**: `app/services/writing_service.py` 重构为多智能体架构；新增 `app/services/writing_pipeline.py`、`app/services/citation_verifier.py`、`app/services/latex_processor.py`、`app/services/diff_engine.py`
- **前端**: `WritingPage.tsx` 大幅重构，新增 Diff 视图组件、项目管理面板、Pipeline 进度可视化
- **API**: `/api/writing/*` 路由升级，新增 `/api/writing/pipeline/*`、`/api/writing/projects/*` 端点
- **依赖**: 新增 `latexdiff`（LaTeX 对比）、`pybtex`（BibTeX 增强）、`difflib`（文本 diff）
- **数据库**: 新增 `WritingProject`、`WritingSection`、`PolishVersion` 模型
