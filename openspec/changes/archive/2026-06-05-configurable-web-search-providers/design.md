# Context

现有联网增强已经具备多查询规划、跨来源去重和引用输出，但检索来源固定为 Bing 与 DuckDuckGo HTML。HTML 来源适合作为零配置保底，不适合作为生产环境唯一入口。

# Goals

- 支持无需改代码即可启用结构化搜索来源。
- 保留当前零配置可用性。
- 避免为了补足少量结果无上限扩大请求量。
- 不向前端和日志暴露 API Key。

# Decisions

## Provider tiers

结构化来源作为 primary tier，按环境变量自动启用：

- `SEARXNG_API_URL`
- `TAVILY_API_KEY`
- `EXA_API_KEY`
- `BRAVE_SEARCH_API_KEY`

Bing 与 DuckDuckGo HTML 作为 fallback tier。若 primary tier 未配置、整体失败或去重后结果少于目标数量，则执行 fallback tier 补足结果。

## Shared result contract

所有 provider 适配器输出 `WebSearchResult`。聚合器继续使用规范化 URL 去重，因此聊天和论文页无需感知来源差异。

## Bounded fan-out

查询数量仍由 `quick`、`standard`、`deep` 三档限制。每个已启用 provider 针对规划查询执行有界请求，不引入递归检索。

## Configuration visibility

设置接口只返回 provider 名称列表。API Key 保留在环境变量中。

# Risks

- 同时配置多个付费来源会增加 API 消耗。通过有界查询数量控制开销。
- provider JSON 字段可能调整。每个适配器独立解析并在异常时返回空结果，让聚合器继续降级。

