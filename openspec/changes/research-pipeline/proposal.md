## Why

系统的核心价值是辅助科研全流程。在已建立论文知识库和 RAG 引擎的基础上，需要实现自动化科研 Pipeline：分析现有论文研究 gap → 生成创新性 Idea → 多轮讨论细化 → 生成实验代码框架。

## What Changes

- Idea 生成服务：基于知识库中指定方向的论文，调用 LLM 分析 research gap 并生成创新想法
- Idea 讨论 API：多轮对话接口，支持引用论文、逐步细化 Idea
- 代码生成服务：将确定的 Idea 转化为实验代码框架（PyTorch 模板）
- 前端研究项目管理页面：创建研究方向、查看 Idea 列表、讨论区、代码预览
- 数据库模型：研究方向项目、Idea 记录表

## Capabilities

### New Capabilities

- `idea-generation`: 基于知识库论文的 Idea 自动生成
- `idea-discussion`: 多轮 Idea 讨论与细化
- `code-generation`: 实验代码框架生成
- `research-project`: 研究方向项目管理和数据库模型
