## 1. Generic Runtime

- [x] 1.1 Add shared chat tool models for calls, observations, trace events, tool definitions, and runtime state.
- [x] 1.2 Add a shared tool registry with schema export, argument validation, unknown-tool rejection, and side-effect policy checks.
- [x] 1.3 Add a bounded runtime loop with max steps, stop reasons, exception capture, and trace event collection.
- [x] 1.4 Add strict JSON tool plan parsing and deterministic fallback planning for the initial research tools.

## 2. Initial Tools

- [x] 2.1 Implement `search_papers` by reusing existing scholarly paper search services with bounded results.
- [x] 2.2 Implement `search_library` by reusing existing RAG/hybrid library search with bounded references.
- [x] 2.3 Implement `import_paper` as a side-effect tool that returns `waiting_confirmation` unless the user explicitly confirms the exact pending action.
- [x] 2.4 Ensure tool observations can produce references and compact context blocks for the final LLM answer.

## 3. Chat API Integration

- [x] 3.1 Integrate the generic runtime into chat send/stream paths without regressing Research Scout mode.
- [x] 3.2 Stream or attach generic tool trace metadata using the existing frontend trace schema where possible.
- [x] 3.3 Add a confirmation endpoint or action path for pending side-effect tool calls.
- [x] 3.4 Persist or reconstruct enough pending-action metadata to validate user ownership and session scope before confirmation.

## 4. Frontend

- [x] 4.1 Extend the existing collapsed tool trace UI for `waiting_confirmation` status.
- [x] 4.2 Render confirmation actions for pending `import_paper` tool calls.
- [x] 4.3 Preserve existing Research Scout candidate cards, source strip collapse, and manual scroll behavior.

## 5. Verification

- [x] 5.1 Add backend tests for registry schema export, invalid tool rejection, argument validation, bounded execution, and side-effect blocking.
- [x] 5.2 Add backend tests for `search_papers`, `search_library`, and confirmed `import_paper` observations using existing service seams or mocks.
- [x] 5.3 Add chat streaming tests for generic tool trace metadata.
- [x] 5.4 Add frontend contract tests for waiting-confirmation tool traces and import confirmation actions.
- [x] 5.5 Run OpenSpec validation, focused backend tests, frontend contract tests, and frontend build.
