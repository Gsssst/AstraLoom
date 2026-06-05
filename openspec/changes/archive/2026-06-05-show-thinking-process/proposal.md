## Why

DeepSeek V4 Pro 是推理模型，默认开启思考模式（thinking mode）。模型在生成回答前会先进行深度推理，这部分思考过程通过 `reasoning_content` 字段返回。目前系统完全丢弃了思考过程，只展示最终回答——用户无法看到模型的推理逻辑，也无法判断模型是否在"认真思考"还是"卡住了"。参考 GPT Academic、ChatGPT、Claude Code 等产品的做法，应支持可选展示思考过程。

此外，当前 `max_tokens` 设置过低（3072-8192），而 DeepSeek 官方文档明确指出 `reasoning_content` 与 `content` 共享 `max_tokens` 预算，默认值需要大幅提升（上限 384K）。

## What Changes

- **LLM 服务升级**: 显式开启 `thinking: {type: "enabled"}`，新增 `chat_stream_with_thinking` 方法返回结构化事件 `{type: "reasoning"|"content", content: "..."}`
- **max_tokens 默认值修正**: `chat` 默认 16384，`chat_stream` 默认 16384，`chat_stream_with_thinking` 默认 32768，失败时自动升级到 65536
- **思考过程展示开关**: 所有对话/写作/论文问答流式 API 新增 `show_thinking: bool` 参数，为 true 时返回思考过程
- **前端 ThinkingPanel 组件**: 可折叠的思考过程面板，使用等宽字体灰色展示，默认折叠（仅显示"思考中..."状态指示器），用户点击展开查看完整推理
- **写作助手集成**: Writing Pipeline 的 Writer Agent 使用 `chat_stream_with_thinking`，支持在写作结果中嵌入思考过程

## Capabilities

### New Capabilities

- `thinking-display`: 思考过程展示 — LLM 流式响应的 reasoning_content 捕获、SSE 传输、前端折叠面板展示

### Modified Capabilities

- `writing-pipeline`: Writer Agent 使用 `chat_stream_with_thinking` 以支持思考过程输出

## Impact

- **后端**: `app/services/llm.py` — 新增 `chat_stream_with_thinking` 方法；`app/api/chat.py`/`chat_sessions.py`/`papers.py` — 流式端点新增 `show_thinking` 参数
- **前端**: 新增 `ThinkingPanel` 组件；`ChatPage`/`PaperDetailPage`/`WritingPage` — 集成思考过程展示
- **无数据库变更**
