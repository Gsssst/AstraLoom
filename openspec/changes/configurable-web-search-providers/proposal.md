# Why

联网增强目前只抓取 Bing 与 DuckDuckGo 的 HTML 搜索页。该方案无需配置，但页面结构变化、反爬限制和区域差异都会影响稳定性，也缺少面向 LLM 检索的结构化摘要。开源研究助手通常将可配置搜索服务或元搜索服务放在主链路，并保留降级能力。

# What Changes

- 增加可配置的结构化联网搜索来源：SearXNG、Tavily、Exa、Brave Search。
- 配置了结构化来源时优先查询结构化 API；未配置、请求失败或结果不足时，回退到现有 Bing 与 DuckDuckGo HTML 检索。
- 复用统一的 `WebSearchResult` 数据结构，对不同来源做 URL 规范化和跨来源去重。
- 在系统设置接口中返回当前可用的联网搜索来源名称，不暴露 API Key。
- 为来源选择、结构化解析、失败降级和去重增加自动化测试。

# Capabilities

## New Capabilities

- `configurable-web-search-providers`: 支持可配置的结构化搜索来源和零配置 HTML 降级链路。

## Modified Capabilities

- None.

# Impact

- Backend: `app/services/web_search.py`, `app/core/config.py`, `app/api/settings.py`
- Deployment: `.env.example`, `docker-compose.yml`
- Tests: `backend/tests/test_web_search_reliability.py`

