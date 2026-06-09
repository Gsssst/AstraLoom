## Context

The Toolbox MVP lets users select tools for idea generation, and the backend stores a compact `tool_context`. Candidate prompts currently receive that raw context directly. This is useful but weak: it does not map tools to gaps, assign roles, or make the model explain why a selected tool is relevant.

Recent open-source research-agent patterns such as AI-Scientist, Curie, and CoI-Agent separate ideation from experiment/tool planning. This change applies that pattern in a smaller deterministic form: build a role-aware tool fit plan before asking the model to generate or evolve candidates.

## Goals / Non-Goals

**Goals:**

- Build a compact `tool_fit_plan` from project brief, Gap Map, selected toolbox entries, and tool mode.
- Use deterministic scoring so the plan is fast, inspectable, and testable.
- Feed the plan into candidate generation and fallback generation.
- Persist tool-fit rationale on selected proposals and run review summary.
- Show proposal-level tool-fit rationale in the existing research project UI.

**Non-Goals:**

- No new database tables or migrations.
- No automatic extraction of tools from papers.
- No graph database or full tool knowledge graph.
- No additional long-running LLM stage before every generation run.

## Decisions

### Deterministic fit plan

Use a helper such as `build_tool_fit_plan(brief, gap_map, generation_context)` that returns:

- `mode`: selected tool mode.
- `items`: ranked selected tools with `fit_score`, `role`, `matched_gap_titles`, `rationale`, `risk_note`, `recommended_use`.
- `summary`: concise instruction for prompt and UI.

Scoring uses simple lexical overlap across project name/description/keywords, gap title/question/opportunity/limitation, tool name/summary/use cases/tags, and linked paper evidence notes. This keeps the algorithm reproducible and cheap.

### Role assignment

Role is derived from both `tool_mode` and tool kind:

- `required`: `core_component` unless the kind is dataset/metric, where it becomes `required_evaluation_asset`.
- `baseline`: `baseline_or_comparator`.
- `avoid`: `avoid_or_contrast`.
- `inspiration`: `inspiration` by default, with dataset/metric mapped to `evaluation_asset`.

This gives the model clearer constraints than raw text.

### Prompt integration

`_format_generation_constraints` will include `tool_fit_plan` alongside `tool_context`. Candidate and evolution prompts will ask the model to follow the plan and return `used_tool_ids`, `used_tool_names`, and optional `tool_fit_rationale`.

Fallback candidates will use the top-ranked plan item so generation still behaves sensibly when the LLM returns invalid JSON.

### Persistence and UI

Selected proposals store `tool_fit_plan`, `used_tool_ids`, `used_tool_names`, and `tool_fit_rationale` inside `review_json`. The project page displays this in proposal details as a small "工具适配" section.

## Risks / Trade-offs

- [Risk] Lexical matching may miss semantically relevant tools with different wording. → Keep raw `tool_context` in the prompt and make scoring a guide, not a hard filter.
- [Risk] Required mode could force a weak tool into an idea. → Still include fit score and risk notes so users can see poor matches.
- [Risk] UI could become crowded. → Display only the selected proposal's concise tool-fit rationale, not the full plan by default.
