## Why

LLM API 偶尔因网络抖动或限流返回错误，当前直接显示"发送失败"，用户体验差。需要自动重试机制。

## What Changes

- LLM 调用失败时自动重试 1 次（间隔 2 秒）
- 前端显示重试状态"正在重试..."
- 两次均失败才显示错误

## Capabilities

### New Capabilities

- `auto-retry`: LLM 调用自动重试
