## Context

General chat now runs an LLM tool planner in normal mode. That is useful for agent-like behavior, but it also changes latency and predictability. Mature agent products expose control surfaces for similar reasons: OpenHands lets users choose how much agent autonomy to invoke, LangGraph designs human control into state transitions, LibreChat makes agent/tool surfaces configurable, and Open WebUI separates function/pipeline availability from normal chat.

This change adds a small per-turn tool mode control instead of a broad settings page.

## Goals / Non-Goals

**Goals:**

- Let users choose `auto`, `off`, or `force` for generic chat tools from the composer.
- Submit that mode in both stream and non-stream chat requests.
- Make backend planner gating deterministic and testable.
- Preserve Research Scout routing and UI because it is a separate assistant mode.
- Keep the default behavior as `auto`.

**Non-Goals:**

- Per-user persisted preferences.
- A full tool marketplace or per-tool allowlist UI.
- Replacing Research Scout mode.
- Streaming every planner micro-event before final answer generation.

## Decisions

### Decision: Add `tool_mode` to `SendMessageRequest`

Use a validated literal field:

- `auto`: current planner behavior.
- `off`: skip generic planner/tools.
- `force`: run planner and force deterministic fallback if planner returns no actions or invalid output and a deterministic plan exists.

Rationale: a request field is explicit, easy to test, and does not require a database migration.

### Decision: Keep Research Scout independent

When `effective_mode == "research_scout"`, generic `tool_mode` does not affect the Research Scout pipeline.

Rationale: Research Scout has its own domain-specific planner and candidate-card contract.

### Decision: Implement force mode inside planner call options

Add a planner flag such as `force_fallback` so force mode can reuse the same planner service but override fallback behavior for no-action cases.

Rationale: this keeps policy in one planner service instead of scattering it through `chat_sessions.py`.

### Decision: Use compact composer control

Add a small select/segmented control near existing mode/retrieval controls. Labels should be concise:

- `自动工具`
- `禁用工具`
- `强制工具`

Rationale: this is a workbench, not a settings page; users need per-turn control while typing.

## Risks / Trade-offs

- **Force mode still cannot invent deterministic actions for vague prompts** -> Show trace/fallback only when actions exist; otherwise answer normally.
- **More controls can clutter the composer** -> Use compact labels and avoid new modal/settings UI.
- **Users may expect force mode to override Research Scout** -> Keep mode label clear and document that Research Scout remains dedicated.
- **Planner costs in auto mode** -> Users can choose off mode when they want fast normal chat.
