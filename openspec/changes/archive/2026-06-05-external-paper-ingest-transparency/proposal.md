## Why

论文库已经支持 arXiv、Semantic Scholar、OpenAlex、Google Scholar 等来源，但用户仍然难以判断一次外部检索到底用了哪些来源、哪些来源失败、哪些结果有开放 PDF、入库后会进入哪个分类。外部检索与入库需要更透明，才能减少“搜不到是不是系统坏了”的疑惑。

## What Changes

- 外部检索结果页展示来源透明度：当前来源策略、多源覆盖说明、失败来源提示。
- 远程论文卡片强化开放 PDF、来源链接、入库目标分类和“已入库/可入库”状态。
- 综合学术检索时明确提示多源混合结果来自哪些 provider，并在结果为空时给出下一步建议。
- 入库完成后刷新分类诊断和维护中心状态，让用户知道新论文是否改善分类/知识库质量。

## Capabilities

### New Capabilities
- `external-paper-ingest-transparency`: Covers transparent external paper search and ingest UX, including provider visibility, open-PDF status, target collection clarity, and empty-result guidance.

### Modified Capabilities

## Impact

- Paper library frontend search/result cards.
- Existing paper search and ingest APIs are reused.
- Frontend contract tests for provider transparency and ingest status.
