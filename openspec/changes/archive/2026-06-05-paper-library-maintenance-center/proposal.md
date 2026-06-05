## Why

知识库维护能力已经存在，但主要藏在设置页，论文库用户在遇到“检索不到、论文问答证据不足、分类不适合生成 idea”时，很难第一时间看到原因和修复动作。需要把维护入口放回论文库，让用户在管理论文的同一页面看到全库健康、分类健康和检索诊断。

## What Changes

- 在论文知识库页面新增维护中心视图，管理员可查看全文覆盖、向量覆盖、BM25 状态、缺全文/缺向量样本。
- 维护中心展示系统推荐修复动作，并允许管理员直接执行重建 BM25、补全文、补向量。
- 维护中心提供检索诊断入口，解释 BM25/Dense/Hybrid 为什么命中或没命中。
- 分类健康信息从“选择分类时的提示”提升为维护中心的一部分，集中展示哪些分类不适合作为 idea 语料。
- 普通用户看到维护中心说明，但具体修复动作仍受管理员权限保护。

## Capabilities

### New Capabilities
- `paper-library-maintenance-center`: Covers a paper-library maintenance center that centralizes retrieval health, repair recommendations, search diagnostics, and collection readiness.

### Modified Capabilities

## Impact

- Frontend paper library page.
- Existing paper maintenance and folder diagnostics APIs are reused.
- Frontend contract tests for paper library maintenance visibility.
