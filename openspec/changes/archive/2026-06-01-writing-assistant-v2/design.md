## Context

当前写作助手（`writing_service.py`）的 8 个功能全部采用"RAG 检索 → 单次 LLM Prompt → 文本输出"的线性模式。每次调用是独立的、无状态的、单阶段的。参考 GPT Academic (70k+ Stars)、ScholarCopilot (COLM 2025)、OpenDraft (19 Agent Pipeline)、Full_Text_RWG (ACL 2025)、TexGuardian、STORM 等开源项目的最佳实践，需要将架构升级为多阶段、多智能体协作、有状态、支持迭代改进的写作工作站。

**当前技术栈约束**：
- 后端: Python 3.12, FastAPI, SQLAlchemy async, LiteLLM (DeepSeek V4 Pro)
- 前端: React 19, TypeScript, Ant Design 6, Zustand
- 现有 RAG 服务 (`RAGService`)、LLM 服务 (`llm_service`) 可直接复用

## Goals / Non-Goals

**Goals:**
1. 建立多智能体 Pipeline 引擎，协调 Selector/Reader/Writer/Reviewer/Citation 五个 Agent
2. 所有写作 API 支持 SSE 流式输出，前端实时展示 Pipeline 各阶段进度
3. 实现 Diff 视图润色：unified diff 展示 + 逐条 accept/reject + 多轮迭代
4. 引用真实性验证：交叉核验 Semantic Scholar + CrossRef + arXiv
5. LaTeX 感知处理：润色时自动保护公式/引用/图表环境
6. 写作项目管理：章节组织、进度追踪、多格式导出、模板管理

**Non-Goals:**
- 不训练/微调专用写作模型（使用现有 DeepSeek V4 Pro + Prompt Engineering）
- 不实现实时多人协作（CRDT/OT 过于复杂，放到后续版本）
- 不实现完整的 LaTeX 编译器（仅做编译校验，不做完整的 PDF 渲染管线）
- 不替换现有 `/api/writing/*` API 签名（向后兼容，新增 `/api/writing/pipeline/*` 端点）

## Decisions

### D1: Pipeline 架构 — 五智能体协作模式

**选择**: Selector → Reader → Writer → Reviewer → Citation 五智能体，以 Writer 为中心、其他为辅助的星型协作架构。

**理由**:
- OpenDraft 使用 19 个 Agent 的线性 Pipeline（Research→Structure→Write→Cite→Polish→Export），适合从头生成整篇论文
- Full_Text_RWG 使用 3 个 Agent（Selector/Reader/Writer）专门做 Related Work，协作更紧密
- 我们的场景介于两者之间：既有完整论文写作需求，也有单段落生成需求
- 五智能体星型架构：Writer 是核心，Selector 和 Reader 为 Writer 提供素材，Reviewer 和 Citation 对 Writer 输出做质量控制
- 比 OpenDraft 的 19 Agent 更简洁，比 Full_Text_RWG 的 3 Agent 更全面

**备选方案与不选理由**:
- 线性 6 阶段 Pipeline（OpenDraft 模式）：过于僵化，不适合"润色一段文字"这类轻量任务
- 单一 LLM + 长 Prompt：最简单但输出质量不稳定，无法做引用验证
- LangChain/LlamaIndex Agent 框架：引入重依赖，过度抽象

### D2: Agent 实现方式 — 基于 Prompt Engineering 的轻量 Agent

**选择**: 每个 Agent 是一个 Python 类，封装专用的 System Prompt + 工具调用（RAG 检索、API 验证），共享同一个 LLM 实例。

**理由**:
- 不需要训练专用模型（ScholarCopilot 的 7B 模型需要大量资源）
- DeepSeek V4 Pro 已有强大的推理和写作能力，Prompt Engineering 足以引导行为
- 轻量实现，每个 Agent 类 ~100-200 行，维护成本低

**Agent 职责定义**:
```
SelectorAgent:  分析用户写作意图 → 决定需要哪些素材 → 调用 RAG/Web Search
ReaderAgent:    深度阅读指定论文/章节 → 提取关键信息 → 更新工作记忆
WriterAgent:    基于记忆和素材 → 生成写作内容（段落/章节/全文）
ReviewerAgent:  审阅 Writer 输出 → 提出修改建议（逻辑/语言/结构）
CitationAgent:  提取 Writer 输出中的引用 → 交叉验证真实性 → 标记状态
```

### D3: Pipeline 引擎设计 — 异步流式编排

**选择**: 使用 Python `asyncio.Queue` 实现事件驱动的 Pipeline 引擎，每个 Agent 的输出通过队列流向下一阶段，同时通过 SSE 推送进度事件到前端。

**架构图**:
```
用户请求 → PipelineEngine
              ├─ Phase 1: Selector → 检索素材 (SSE: "researching")
              ├─ Phase 2: Reader   → 深度阅读 (SSE: "reading")
              ├─ Phase 3: Writer   → 生成内容 (SSE: "writing", tokens流式)
              ├─ Phase 4: Reviewer → 审阅建议 (SSE: "reviewing")
              └─ Phase 5: Citation → 验证引用 (SSE: "verifying")
```

**Pipeline 配置**:
- 轻量任务（润色/摘要）：仅 Writer → Reviewer，~2-3 阶段
- 标准任务（Related Work/文献综述）：Selector → Reader → Writer → Citation，~4-5 阶段
- 重量任务（完整论文章节）：全部 5 阶段

### D4: Diff 引擎 — difflib + LaTeX 感知

**选择**: 使用 Python 标准库 `difflib.SequenceMatcher` 生成 unified diff，增加 LaTeX 感知的预处理层。

**处理流程**:
```
原文 + 润色文 → LaTeX Block Detector (标记受保护块) 
             → SequenceMatcher (逐句/逐段对比)
             → Diff Formatter (生成 unified diff)
             → SSE 推送 diff hunks 到前端
```

**LaTeX 保护规则**（参考 GPT Academic）:
- `$...$` / `$$...$$` — 行内/行间公式
- `\cite{...}` / `\ref{...}` / `\label{...}` — 引用和标签
- `\begin{figure}...\end{figure}` — 浮动环境
- `\begin{table}...\end{table}` — 表格环境
- `\begin{equation}...\end{equation}` — 公式环境

### D5: 引用验证 — 多源交叉核验

**选择**: 并行查询 Semantic Scholar API + CrossRef API + arXiv API，2/3 一致视为"已验证"。

**验证逻辑**:
```
提取引用 → 并行查询 3 个 API
         ├─ 3/3 或 2/3 匹配 → ✅ 已验证 (verified)
         ├─ 1/3 匹配       → ⚠️ 待核实 (uncertain)  
         └─ 0/3 匹配       → ❌ 疑似幻觉 (likely_hallucination)
```

**备选方案**: 使用 OpenAlex（免费、大数据量）替代 CrossRef。选择 CrossRef 因为其 DOI 数据最完整，Semantic Scholar 的引用关系最好。

### D6: 数据模型 — 新增 3 个表

**WritingProject**: 写作项目（标题、模板类型、状态、用户 ID）
**WritingSection**: 项目章节（名称、内容、排序、状态）
**PolishVersion**: 润色版本（关联章节、原文、润色文、diff、用户操作记录）

使用 UUID 主键 + TimestampMixin，与现有 BaseModel 一致。

### D7: 前端架构 — 保持 Ant Design + Zustand

**选择**: 不引入新的 UI 框架。Diff 视图使用自定义组件（基于 `<diff>` HTML 语义 + CSS），Pipeline 进度使用 Ant Design `Steps` 组件，项目管理使用 Ant Design `Tree` + `Card`。

## Risks / Trade-offs

- **[风险] Prompt Engineering 的 Agent 输出质量不稳定** → 缓解：每个 Agent 的 System Prompt 包含严格的输出格式约束（JSON Schema），输出前做格式校验，失败自动重试
- **[风险] 多 Agent 调用增加延迟** → 缓解：轻量任务可跳过不需要的 Agent；支持用户中断；前端展示实时进度避免用户焦虑
- **[风险] 外部 API (Semantic Scholar/CrossRef/arXiv) 限流** → 缓解：本地缓存验证结果（24 小时 TTL）；优雅降级（API 不可用时标记为"待核实"而非报错）
- **[风险] LaTeX 解析不完整（复杂宏/自定义命令）** → 缓解：使用白名单方式（只保护明确的 LaTeX 环境），不在白名单中的交由 LLM 自行处理
- **[权衡] 引用验证的准确度 vs. 实现复杂度** → 选择 2/3 多数投票策略，简单有效。不做模糊匹配（作者名相似度、标题编辑距离）以降低复杂度

## Open Questions

1. 写作模板（ACL/CVPR/NeurIPS/NSFC）的 LaTeX 文件是否需要预置在项目中？→ 建议仅提供 Markdown 大纲模板，LaTeX 样式文件由用户自行管理
2. 多轮润色的版本存储上限？→ 建议最近 10 个版本，超出的自动清理
3. 是否需要支持用户自定义 Agent Prompt？→ 放到 v2.1，先使用预设 Prompt
