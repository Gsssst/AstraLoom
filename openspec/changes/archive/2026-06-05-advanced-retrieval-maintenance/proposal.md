## Why

The first retrieval maintenance console shows coverage and lets administrators run repair actions, but it still leaves a gap: when a query misses, users need to know whether the cause is lexical mismatch, missing embeddings, missing full text, stale BM25, or simply no good local source. AI answers should also disclose when they are operating with low retrieval coverage instead of sounding equally confident.

## What Changes

- Extend search diagnostics with query terms, branch-level explanations, and actionable next steps.
- Add an administrator recommendations endpoint that prioritizes papers needing full-text parsing, embedding generation, or BM25 rebuild.
- Surface these recommendations in the settings maintenance panel.
- Add transparent retrieval-quality status messages to chat and paper AI Q&A when local retrieval coverage is low or no supporting sources are available.
- Add regression tests for explanations, recommendations, and low-coverage status text.

## Capabilities

### New Capabilities
- `advanced-retrieval-maintenance`: Defines explainable diagnostics, repair recommendations, and transparent low-coverage answer status.

## Impact

- Affected backend modules: paper API, chat session retrieval status, hybrid search service usage.
- Affected frontend modules: settings data tab maintenance panel.
- No database migration is required.
