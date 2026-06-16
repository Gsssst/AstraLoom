## Context

The previous change added a shared chat tool runtime with typed tools, side-effect confirmation, and trace persistence. That runtime currently depends on deterministic trigger rules for ordinary chat. Mature agent systems use a stronger pattern:

- OpenHands separates agent actions from observations and surfaces the same agent core through multiple interfaces.
- LangGraph makes state explicit, supports bounded state transitions, and treats human-in-the-loop confirmation as a first-class control point.
- LibreChat exposes agents, tools, MCP servers, and skills through configurable tool surfaces.
- Open WebUI keeps tool/function execution pluggable while the UI displays execution feedback separately from answer prose.

The local system should adopt the same action/observation shape without introducing arbitrary code execution or replacing the specialized Research Scout workflow in this slice.

## Goals / Non-Goals

**Goals:**

- Let the LLM choose from registered chat tools using schema-aware strict JSON plans.
- Execute model-planned calls through the existing `ChatToolRegistry` and `ChatAgentToolRuntime`, never by trusting raw model text.
- Feed compact observations back into a bounded planning loop so the model can perform multi-step retrieval before the final answer.
- Preserve deterministic fallback planning when the LLM planner returns invalid JSON, unavailable tools, invalid arguments, or no useful plan.
- Preserve confirmation gates for side-effect tools such as `import_paper`.
- Emit planner and tool trace metadata compatible with the current collapsed trace UI.
- Keep Research Scout prompts on the current Research Scout agent path to avoid regressions in paper-candidate cards and ranking.

**Non-Goals:**

- Native provider function-calling integration.
- MCP server marketplace support.
- Arbitrary shell, browser, or Python execution.
- Long-running resumable background agent jobs.
- Replacing Research Scout with the generic planner.
- Adding new document or multimodal tools in this change.

## Decisions

### Decision: Add a planner layer instead of folding planning into each tool

Create a small service, likely `backend/app/services/chat_tool_planner.py`, that owns prompt construction, JSON parsing, fallback selection, and loop orchestration. Tool execution remains in `chat_agent_tools.py`.

Rationale: this keeps tool validation and side-effect policy centralized while making the planner replaceable later with native function calling or LangGraph-style state graphs.

Alternatives considered:

- Put planner logic in `chat_sessions.py`: simpler initially but would make API code responsible for agent state and parsing.
- Put planner logic into `ChatAgentToolRuntime`: would blur execution policy with model prompting and make deterministic execution harder to test.

### Decision: Use strict JSON actions with an explicit final-answer signal

The planner prompt asks the model to return one JSON object:

```json
{
  "actions": [
    {"tool": "search_library", "arguments": {"query": "...", "limit": 5}, "thought_summary": "..."}
  ],
  "final": false,
  "final_context_summary": ""
}
```

When the model has enough observations, it can return `{"actions": [], "final": true, ...}`. The backend validates every action before execution.

Rationale: strict JSON is provider-agnostic and works with the existing LLM service. It also gives deterministic tests around parser behavior.

Alternatives considered:

- Provider-native tool/function calling: better long term, but current app supports multiple providers and the first planner should not couple to one API.
- Free-form ReAct text parsing: more flexible but less reliable and harder to validate safely.

### Decision: Bound the planner loop tightly

The first implementation should use small budgets: for example 2 planner rounds and up to 4 tool calls total. Stop reasons should include `completed`, `max_rounds`, `planner_invalid`, `no_actions`, `waiting_confirmation`, and `fallback_used`.

Rationale: research tools can be slow or network-bound; tight budgets prevent poor UX and runaway costs.

Alternatives considered:

- Unbounded planning until the model says stop: too risky for latency and cost.
- Single-shot planning only: safer but not enough to support action/observation behavior.

### Decision: Keep deterministic fallback as the safety net

If planner output is empty, invalid, or fully rejected, the system falls back to the existing deterministic plan from `deterministic_chat_tool_plan`.

Rationale: the previous deterministic route already works for obvious library search, paper search, and explicit import. Keeping it avoids making common prompts worse when the model planner misbehaves.

### Decision: Trace planner events separately but reuse the existing UI shape

Planner events should be represented as trace steps using labels like `规划工具`, `执行工具`, and statuses such as `planned`, `running`, `completed`, `rejected`, or `waiting_confirmation`. No new frontend surface is required unless a status is missing.

Rationale: the trace UI is already collapsed by default and supports result counts and statuses. Extending it minimally reduces UI churn.

### Decision: Do not route Research Scout through the generic planner yet

`effective_mode == "research_scout"` continues using the Research Scout agent and candidate card pipeline.

Rationale: Research Scout has domain-specific query expansion, arXiv-first enrichment, venue/institution filtering, LLM scoring, and candidate card UI. Replacing it now would be a regression risk.

## Risks / Trade-offs

- **Planner hallucinated tools or args** -> Validate tool names and Pydantic args before execution; reject unsafe calls and fallback when needed.
- **Latency increases from planner LLM calls** -> Use small round budgets, compact observations, and deterministic fallback for obvious prompts.
- **Model claims side effects were completed** -> System prompt must forbid this; backend still blocks side-effect execution without confirmation.
- **Trace becomes noisy** -> Keep trace collapsed by default and summarize planner rounds.
- **Provider-specific JSON reliability varies** -> Use strict extraction and robust parse errors; tests should cover malformed JSON and fenced JSON.
- **Research Scout regression** -> Gate generic planner off for `research_scout` mode and preserve existing contract tests.

## Migration Plan

1. Add planner service and parser tests behind existing general-chat flow.
2. Wire planner into non-stream and stream paths only for general mode.
3. Keep deterministic fallback path and existing tool runtime behavior.
4. Verify with backend planner tests, chat coordination tests, frontend contract tests, OpenSpec strict validation, and frontend build.
5. Rollback by disabling planner integration and leaving deterministic tool runtime in place.

## Open Questions

- Should planner enablement be configurable per user or environment after the first implementation?
- Should future planner rounds be surfaced as separate stream events before final answer generation?
- Which next tool should be added first after the planner loop is stable: `read_pdf`, `extract_docx`, or `run_skill`?
