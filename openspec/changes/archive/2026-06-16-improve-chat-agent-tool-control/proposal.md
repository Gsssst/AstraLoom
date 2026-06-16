## Why

The LLM tool planner now gives ordinary chat agent-like behavior, but always letting the model decide can add latency and surprise users who want a purely conversational answer. Users need explicit control over whether chat tools are disabled, automatic, or forced for the current turn.

## What Changes

- Add a chat tool mode control with three values:
  - `auto`: planner decides whether tools are useful.
  - `off`: no generic planner/tool calls are made; chat answers from normal context only.
  - `force`: planner must attempt tool planning, and if it produces no actions the backend falls back to deterministic planning when possible.
- Add the selected tool mode to chat send and stream payloads.
- Add a compact frontend control in the chat composer so users can switch tool behavior without leaving the input surface.
- Reflect the active mode in the composer/runtime label and tool trace metadata.
- Preserve Research Scout behavior: paper-hunting mode still uses the dedicated Research Scout flow regardless of generic tool mode.

## Capabilities

### New Capabilities

### Modified Capabilities

- `llm-tool-planner`: Planner execution SHALL respect an explicit user-selected tool mode for auto/off/force behavior.
- `chat-retrieval-mode-coordination`: Chat UI and request payloads SHALL expose and submit the selected tool mode while preserving existing retrieval and Research Scout routing.

## Impact

- Backend chat request schema and planner gating in `chat_sessions.py`.
- Planner fallback behavior in `chat_tool_planner.py` if force mode requires deterministic fallback when no planner actions are produced.
- Frontend chat composer controls, request payloads, and contract tests.
- Backend tests for `tool_mode` validation and routing behavior.
