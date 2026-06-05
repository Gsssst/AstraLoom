# action-center-maintenance-quick-actions

## Why

The action center currently explains what should happen next, but knowledge-base maintenance actions still require users to manually navigate into settings and find the correct control. This weakens the "next best action" value of the page, especially after retrieval diagnostics already identify missing full text or missing embeddings.

## What Changes

- Extend workflow action items with executable action metadata.
- Mark knowledge-base full-text and embedding maintenance recommendations as bounded admin maintenance API actions.
- Update the action center frontend so users can execute those maintenance actions directly, see a result summary, and still navigate to the detailed settings page when needed.
- Keep existing navigation-only workflow actions unchanged.

## Non-Goals

- Changing retrieval ranking or chunking algorithms.
- Adding long-running background jobs beyond the existing bounded maintenance endpoints.
- Changing role permissions for maintenance endpoints.

## Reference Patterns

- Similar RAG/research-assistant projects expose ingestion, parsing, chunking, and indexing as explicit maintenance steps rather than hiding them behind chat.
- Production RAG dashboards generally keep corrective actions close to diagnostics, so users can repair missing text or embeddings without hunting through settings.

## Success Criteria

- Workflow action API responses can distinguish navigation actions from executable API actions.
- Action center can run bounded knowledge-base maintenance actions and refresh itself after completion.
- Users get transparent success/error feedback instead of a silent redirect.
- Backend and frontend contract tests cover the executable action metadata.
