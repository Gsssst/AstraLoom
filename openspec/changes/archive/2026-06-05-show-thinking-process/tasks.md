## 1. LLM 服务升级

- [x] 1.1 `chat_stream_with_thinking` 方法 — 返回结构化 `{type, content}` 事件
- [x] 1.2 max_tokens 默认值修正 — chat 16384, chat_stream 16384, with_thinking 32768
- [x] 1.3 显式开启 thinking mode — extra_body: {"thinking": {"type": "enabled"}}
- [x] 1.4 重试逻辑升级 — 16384 → 32768 → 65536

## 2. API 端点更新

- [x] 2.1 `/api/chat/completions` — 流式模式支持 `show_thinking` 参数
- [x] 2.2 `/api/chat-sessions/{id}/send-stream` — 支持 `show_thinking` 参数
- [x] 2.3 `/api/papers/{id}/ask-stream` — 支持 `show_thinking` 参数
- [x] 2.4 `/api/writing/pipeline/stream` — Writer Agent 使用 `chat_stream_with_thinking`

## 3. 前端 ThinkingPanel 组件

- [x] 3.1 创建 `ThinkingPanel` 组件 — 可折叠面板、等宽灰色字体、耗时计时器
- [x] 3.2 创建 `useThinkingStream` hook — 消费 SSE reasoning/content 事件、管理状态
- [x] 3.3 `ChatPage` 集成 — 在消息列表中添加 thinking 展示
- [x] 3.4 `PaperDetailPage` 集成 — 在论文问答中添加 thinking 展示
- [x] 3.5 `WritingPage` 集成 — 在写作生成中添加 thinking 展示

## 4. 全局开关

- [x] 4.1 `useSettingsStore` 添加 `showThinking: boolean` 状态
- [x] 4.2 `SettingsPage` 添加"显示思考过程"开关
- [x] 4.3 前端 API 调用自动读取全局开关默认值
