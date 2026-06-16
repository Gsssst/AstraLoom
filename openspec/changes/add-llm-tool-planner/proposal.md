## Why

The chat tool runtime can execute safe tools, but ordinary chat still relies on deterministic trigger rules instead of letting the model decide which tools to call and in what order. To move closer to Codex/Claude Code-style behavior, chat needs an LLM-driven planner that produces validated actions, observes results, and either continues planning or returns a grounded final answer.

## What Changes

- Add an LLM tool planner for general chat that receives available tool schemas and conversation context, then emits strict JSON actions.
- Add an action/observation loop on top of the existing chat tool runtime with bounded iterations and deterministic fallback behavior.
- Stream or attach planner steps, tool calls, observations, validation failures, and final stop reason into the existing collapsible tool trace UI.
- Preserve side-effect confirmation gates: mutation tools such as `import_paper` remain blocked until explicit user confirmation.
- Preserve Research Scout's specialized flow for paper-hunting prompts until the generic planner is mature enough to replace it safely.
- Add tests for JSON plan parsing, invalid planner output recovery, bounded loop behavior, trace metadata, and fallback to deterministic planning.

## Capabilities

### New Capabilities

- `llm-tool-planner`: Model-driven planning loop for selecting registered chat tools, processing observations, and producing a final answer context.

### Modified Capabilities

- `chat-agent-tool-runtime`: The existing runtime SHALL support being driven by a validated LLM planner while retaining typed schemas, bounded execution, trace events, and confirmation gates.
- `chat-retrieval-mode-coordination`: General chat SHALL be able to include planner-generated tool observations in final-answer context and expose planner trace metadata without regressing Research Scout mode.

## Impact

- Backend chat services and APIs for planner prompt construction, strict JSON parsing, action/observation loop orchestration, and streaming metadata.
- Existing `chat_agent_tools.py` runtime and `chat_sessions.py` send/stream integration.
- Frontend trace rendering only if planner-specific statuses or summaries need small display extensions.
- Backend tests for planner behavior and chat integration contracts.
- No database migration expected; planner trace can reuse the existing tool trace reference metadata pattern.
