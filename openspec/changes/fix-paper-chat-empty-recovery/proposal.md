## Why

Paper-detail AI chat can show "首轮生成未返回正文，正在切换稳定回答模式..." and then still end with "模型本轮未返回可展示内容". This happens when both the primary stream and the recovery stream produce no visible content. Users see an internal recovery state but receive no useful answer.

## What Changes

- Add a final non-streaming stable-answer fallback for paper chat streams after both streaming attempts return no visible content.
- Keep already-emitted content behavior unchanged: if content has started and then fails, emit an interruption warning rather than regenerating.
- Improve tests around empty primary stream and empty recovery stream.
- Keep the existing status event, references, and evidence metadata contract unchanged.

## Impact

- Backend paper chat streaming path in `backend/app/api/papers.py`.
- Regression tests for paper chat empty stream recovery.
