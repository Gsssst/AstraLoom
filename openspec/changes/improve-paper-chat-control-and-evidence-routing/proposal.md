## Why

Paper-detail Q&A still lacks several controls and evidence routes that users expect from a research assistant: users cannot stop a long streamed answer, formula-number questions can retrieve the wrong formula, dataset questions may miss experiment evidence, and novelty questions need complete experiment and ablation context.

## What Changes

- Add stop-generation control to paper-detail streamed Q&A using the same AbortController pattern already used by the main chat workspace.
- Improve formula intent parsing so "公式 1" / "第一个公式" targets numbered or ordered formula evidence instead of the first math-like text in prose.
- Add dataset-oriented evidence routing that prioritizes experiment sections, table evidence, captions, and text mentioning benchmarks/datasets.
- Add novelty-evaluation routing that gathers method, experiment, table, ablation, and limitation evidence together.
- Add tests for cancellation UI hooks, formula target retrieval, dataset evidence retrieval, and novelty evidence packs.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `paper-detail-chat-parity`: Paper-detail chat supports stopping an in-flight streamed answer.
- `paper-qa-evidence-grounding`: Paper Q&A evidence routing recognizes formula-number, dataset, and novelty-evaluation questions.

## Impact

- Affects frontend paper-detail chat streaming controls.
- Affects backend paper evidence planning and retrieval.
- Adds focused backend/frontend tests.
- No database migration or new dependency is required.
