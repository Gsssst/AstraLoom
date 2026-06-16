## Context

The first stage built a strong Research Scout flow:

```
query -> intent -> planned tool sequence -> search/filter/rank/evaluate -> cards -> trace
```

That code proved the product direction but is still tied to Research Scout types. The second stage should generalize the pattern so ordinary chat, document reading, writing, and future skills can call the same class of backend tools.

Mature projects point to the same architecture:

- **OpenHands**: one agentic core can be surfaced through CLI, SDK, and GUI, with actions/observations forming the execution loop.
- **LibreChat**: agents, MCP servers, file citations, code execution, and skills are exposed as configurable tool surfaces instead of hard-coded assistant branches.
- **Open WebUI**: BYOF/functions and pipelines make tool capability pluggable while keeping UI feedback separate from answer prose.
- **LangGraph**: emphasizes explicit state, resumability, human-in-the-loop gates, and observability.

The local implementation should be smaller than those systems but adopt the same shape: typed tools, bounded execution, observable trace, and confirmation gates.

## Goals / Non-Goals

**Goals:**

- Create a shared runtime usable by chat modes, not only Research Scout.
- Represent tools with name, label, argument schema, result schema, side-effect policy, and executor.
- Validate every model-planned tool call before execution.
- Block side-effect tools until the user confirms them.
- Stream trace events in a shape compatible with the existing chat UI.
- Start with research-oriented tools that reuse existing services.

**Non-Goals:**

- Full autonomous browser or shell control.
- Arbitrary user-defined Python execution.
- MCP server marketplace integration in the first slice.
- Replacing the Research Scout UI cards.
- Persisting a long-running background agent job queue.

## Architecture

```
┌────────────────────┐
│ Chat request        │
│ mode + user query   │
└─────────┬──────────┘
          ▼
┌────────────────────┐
│ Tool planner        │
│ LLM JSON plan or    │
│ deterministic plan  │
└─────────┬──────────┘
          ▼
┌────────────────────┐      ┌────────────────────┐
│ Tool runtime        │─────▶│ Tool registry       │
│ budgets + state     │      │ schemas + policies  │
└─────────┬──────────┘      └─────────┬──────────┘
          │                           ▼
          │                 ┌────────────────────┐
          │                 │ Tool executor       │
          │                 │ search/import/etc.  │
          │                 └─────────┬──────────┘
          ▼                           ▼
┌────────────────────┐      ┌────────────────────┐
│ Trace events        │◀─────│ Observation         │
│ streamed to UI      │      │ result + references │
└─────────┬──────────┘      └────────────────────┘
          ▼
┌────────────────────┐
│ Final LLM answer    │
│ with tool context   │
└────────────────────┘
```

## Runtime Model

Add a service such as `backend/app/services/chat_agent_tools.py` with:

- `ChatToolCall`
  - `tool`
  - `arguments`
  - `thought_summary`
  - optional `call_id`
- `ChatToolObservation`
  - `tool`
  - `status`: `planned | running | completed | failed | skipped | rejected | waiting_confirmation`
  - `summary`
  - `result_count`
  - `references`
  - `artifacts`
  - `details`
- `ChatToolTraceEvent`
  - UI-safe event with id, tool, label, status, summary, details.
- `ChatToolDefinition`
  - name, label, args model, executor, side-effect policy, required capabilities.
- `ChatToolRegistry`
  - register/get/schemas/execute.
- `ChatAgentToolRuntime`
  - bounded run loop, max steps, timeout, invalid-call handling, and trace collection.

Research Scout can either keep its current runtime in this phase or incrementally adapt to the generic runtime. The first implementation should avoid a risky rewrite; compatibility adapters are acceptable.

## Initial Tools

1. `search_papers`

   Inputs:
   - `query`
   - `limit`
   - optional `year_from`, `year_to`
   - optional `source`

   Behavior:
   - Reuse `search_scholarly_papers`.
   - Return paper result summaries and references.
   - No import side effects.

2. `search_library`

   Inputs:
   - `query`
   - `limit`

   Behavior:
   - Reuse `RAGService` or existing hybrid search.
   - Return local paper references and compact snippets.

3. `import_paper`

   Inputs:
   - `source`
   - remote id/arxiv id/doi/source url or ingest token.

   Behavior:
   - Side-effect tool.
   - Runtime must return `waiting_confirmation` unless `allow_side_effects=True` and confirmation token matches.
   - Actual import reuses existing paper ingest endpoint/service.

## Planning

First version supports two paths:

- Deterministic routing for obvious requests:
  - paper search -> `search_papers`
  - library lookup -> `search_library`
  - import request -> `import_paper` confirmation.
- LLM JSON planning for richer tool sequences:
  - model receives tool schemas,
  - output must be strict JSON,
  - backend validates tool names and args,
  - invalid plans fall back to deterministic routing.

Native provider tool/function calling can be added later behind the same registry.

## Confirmation Flow

Side effects must not execute during autonomous planning.

```
assistant plans import_paper
        │
        ▼
runtime returns waiting_confirmation
        │
        ▼
UI shows confirmation action
        │
        ▼
user clicks confirm
        │
        ▼
backend executes import_paper with confirmation token
```

The first slice can keep confirmation lightweight: include pending action metadata in assistant message metadata and call a new endpoint that validates ownership/session context before executing.

## Streaming / UI

The backend should emit `meta` or dedicated `tool_trace` stream events whenever tool state changes. The existing collapsible `ChatPage` trace renderer should remain the primary display. It may need small extensions for:

- `waiting_confirmation`
- tool action buttons
- result counts and reference counts.

## Risks / Trade-offs

- **Scope creep**: Keep the first implementation to three tools and one confirmation flow.
- **Tool hallucination**: Validate names and args; reject unknown tools; fallback deterministic plan.
- **Duplicate Research Scout logic**: Avoid rewriting Research Scout until the generic runtime is stable.
- **Unclear side effects**: All mutation tools require confirmation by default.
- **Long latency**: Bound steps and provider calls; stream trace events early.

## Verification

- Backend tests for registry schemas, invalid tool rejection, argument validation, side-effect blocking, and initial tool observations.
- Backend tests for streaming metadata shape if the chat route emits generic tool traces.
- Frontend contract tests for `waiting_confirmation` rendering and existing collapsed trace compatibility.
- OpenSpec strict validation and focused backend/frontend tests.
