## Why
联网搜索增加延迟，可能导致请求超时。

## Fix
- web_search 添加 8 秒超时
- httpx client timeout 从 15s 降至 8s
