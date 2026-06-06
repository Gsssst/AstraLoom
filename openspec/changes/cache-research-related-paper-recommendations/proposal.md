## Why

Opening a research direction can still trigger the related-paper recommendation pipeline every time. That endpoint is useful but expensive because it may call the LLM, semantic retrieval, arXiv, and Semantic Scholar, so repeated page visits should reuse recent recommendations.

## What Changes

- Cache related-paper recommendation results on the research project metadata.
- Serve cached recommendations by default when the project inputs have not changed.
- Add an explicit refresh option so users can recompute recommendations when needed.
- Show cached/refresh state in the related-papers panel without blocking the rest of the workbench.

## Capabilities

### New Capabilities

### Modified Capabilities
- `research-idea-workbench`: Related-paper recommendations should be reusable across visits and manually refreshable.

## Impact

- Backend `/api/research/projects/{project_id}/recommended-papers` query behavior and response shape.
- Research project metadata JSON for cached recommendation results and cache key.
- Frontend related-papers panel in `ResearchProjectPage`.
- Backend and frontend regression tests.
