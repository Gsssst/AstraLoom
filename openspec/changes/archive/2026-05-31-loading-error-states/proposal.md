## Why

部分页面仍用 Spin 而不是 Skeleton 加载，白屏时有发生。需要统一加载和错误状态处理。

## What Changes

- PapersPage、ResearchPage 加载状态改为 Skeleton
- 各页面 API 错误时添加「重试」按钮
- 论文详情页加载失败时显示重试

## Capabilities

### New Capabilities

- `loading-error-states`: 统一加载/错误状态
