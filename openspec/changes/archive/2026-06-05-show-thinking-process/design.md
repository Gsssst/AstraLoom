## Context

DeepSeek V4 Pro 是推理模型，默认开启思考模式。每次调用会先进行深度推理（如分析问题、搜索记忆、评估方案），然后生成最终回答。推理过程通过 `delta.reasoning_content` 在 SSE 流中返回。

当前系统的 `chat_stream` 方法只检查 `reasoning_content` 来判断是否需要增大 `max_tokens`，但**从不向调用者暴露思考内容**。这些宝贵的推理过程被完全丢弃。

参考产品做法：
- **ChatGPT**: 灰字折叠展示 "Thinking..."，用户可展开
- **Claude Code**: 显示 "Thinking (Ctrl+T to toggle)"
- **GPT Academic**: 可选展示中间推理步骤

## Goals / Non-Goals

**Goals:**
1. 在所有流式 LLM 调用中捕获 `reasoning_content`
2. 前端以可折叠面板展示思考过程，默认折叠
3. 提供全局开关控制是否请求/展示思考过程
4. max_tokens 修正为符合 DeepSeek 官方文档推荐的值

**Non-Goals:**
- 不在非流式 API 中展示思考过程（非流式响应已包含完整的思考+回答，拆分为两步增加延迟）
- 不修改 `chat_stream` 的现有签名（向后兼容，新增 `chat_stream_with_thinking` 方法）

## Decisions

### D1: 新增 `chat_stream_with_thinking` 方法

**选择**: 新增独立方法而非修改 `chat_stream`，保持向后兼容。

`chat_stream_with_thinking` 返回结构化事件：
```python
{"type": "reasoning", "content": "让我分析一下这个问题..."}
{"type": "reasoning", "content": "关键是要理解..."}
{"type": "content", "content": "基于以上分析，答案是..."}
```

调用者可根据 `type` 分别处理。

### D2: 思考过程前端展示

**选择**: 可折叠面板（Ant Design Collapse），默认折叠。

```
┌─────────────────────────────────────────┐
│ 💭 思考中... (2.3s)              [展开] │  ← 默认折叠
├─────────────────────────────────────────┤
│ 让我分析一下这个问题...                   │  ← 展开后显示
│ 关键是要理解 video grounding 的本质是...  │     等宽灰色字体
│ ...                                      │
└─────────────────────────────────────────┘
│ 基于以上分析，Video grounding 领域的      │  ← 正常回答
│ 相关工作可以分为以下几类...               │
```

### D3: max_tokens 分级策略

**选择**: 三级 max_tokens 策略

| 场景 | max_tokens | 说明 |
|------|-----------|------|
| 默认（简单问答） | 16384 | 足够大多数场景 |
| 复杂内容生成 | 32768 | 写作/分析任务 |
| 重试上限 | 65536 | 思考耗尽后自动升级 |

DeepSeek 官方上限为 384K，65K 作为应用上限已足够覆盖思考+输出的需求。

### D4: show_thinking 参数

**选择**: 在前端 API 请求中新增 `show_thinking: boolean` 参数。

- `true`: 使用 `chat_stream_with_thinking`，返回思考+内容
- `false`（默认）: 使用 `chat_stream`，仅返回内容（向后兼容）

全局默认值可从前端设置页切换。

## Risks / Trade-offs

- **[风险] 思考过程可能包含敏感信息** → 缓解：默认折叠，用户主动展开才能看到
- **[风险] 思考过程增加网络传输量** → 缓解：默认关闭，用户主动开启
- **[取舍] max_tokens 提升增加单次调用成本** → DeepSeek 当前 75% 折扣，输出仅 $0.87/1M tokens，性价比极高
