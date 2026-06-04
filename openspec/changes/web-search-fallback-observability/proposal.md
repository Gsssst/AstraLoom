## Why

联网增强在未配置结构化 provider 时依赖 Bing 与 DuckDuckGo HTML 页面。当前 Bing 页面结构已经变化，DuckDuckGo 又可能返回拦截页，导致用户开启联网增强后仍然只能得到知识库上下文。

## What Changes

- 为零配置模式增加 Bing RSS 结构化 fallback。
- 保留 HTML provider 作为补充容错来源。
- 在对话和论文问答的流式状态中显示本轮知识库与联网来源数量。
- 为 RSS 解析和联网空结果状态增加回归测试。

## Capabilities

### New Capabilities

- `web-search-fallback-observability`: 稳定的零配置联网 fallback 与可见检索状态。

### Modified Capabilities

- None.

## Impact

- Backend: `app/services/web_search.py`, `app/api/chat_sessions.py`, `app/api/papers.py`
- Tests: web-search reliability and retrieval coordination tests

