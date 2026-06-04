# Context

实测 Bing HTML 搜索页返回 `200`，但不再包含旧版 `b_algo` 节点；DuckDuckGo HTML 可能返回 `202` 拦截页。Bing RSS 对同一查询能返回结构化结果。

# Decisions

## Use Bing RSS as the primary no-key fallback

Bing RSS 使用 XML `item` 节点，字段稳定且无需 API Key。零配置 fallback 将优先使用 RSS，并保留 HTML provider 作为补充来源。

## Expose retrieval counts

检索聚合函数继续返回统一引用列表。流式接口根据引用中的 `source` 统计本地论文和网页来源数量，并将统计写入状态事件。

# Risks

- RSS 结果摘要较短，但比无结果更可靠；高质量场景仍推荐配置 Tavily、Exa、Brave 或 SearXNG。

