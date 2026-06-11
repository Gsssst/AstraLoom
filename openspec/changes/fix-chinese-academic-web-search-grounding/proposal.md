## Why

Chinese academic chat prompts such as "请给我找10篇关于多模态大模型的论文" are currently sent to fallback web providers as full polite sentences, which can cause results about the word "请" or translation pages to appear as citations. This breaks source grounding because the displayed references are not the sources most relevant to the user's research request.

## What Changes

- Normalize Chinese academic search prompts into topic-focused search variants before querying providers.
- Expand common Chinese research topics with useful English aliases where deterministic mappings are available.
- Strengthen relevance filtering so polite/action words and requested counts do not keep unrelated dictionary or translation pages.
- Preserve source auditability by returning the final retained result title, URL, provider, and retrieval query.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `chat-web-research`: web search planning and structured evidence filtering must keep displayed sources aligned with the user's research topic.

## Impact

- Affects backend web search planning and relevance filtering in `backend/app/services/web_search.py`.
- Adds regression coverage in `backend/tests/test_web_search_reliability.py`.
- No database, API schema, or dependency changes.
