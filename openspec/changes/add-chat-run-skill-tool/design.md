## Context

Stage 2 is turning chat from free-form answering into a tool-using agent surface. The current runtime already has typed schemas, trace events, side-effect gates, and planner visibility. Stage 4 will later introduce a full project skill system, but the next useful slice is a safe built-in `run_skill` tool that lets chat invoke repeatable research workflows without adding dynamic code execution.

Mature agent systems share a similar separation: LangChain treats tools and agent planning as explicit runtime surfaces, CrewAI separates agents/tasks/tools as reusable definitions, and AutoGPT exposes reusable agents through a protocol/marketplace pattern. This project should follow the separation, but keep the first implementation local, read-only, and testable.

## Goals / Non-Goals

**Goals:**

- Provide a built-in registry of research skills with id, label, description, allowed tool hints, output format, and evaluation criteria.
- Register `run_skill` as a non-side-effect chat tool.
- Execute a skill by assembling a bounded prompt from the selected skill, user task, optional context, and current query.
- Return structured observation context that the final chat answer can use.
- Reject unknown skills with a clear list of available skill ids.
- Preserve existing planner, trace, and confirmation behavior.

**Non-Goals:**

- Installing external skills or loading arbitrary user-authored code.
- Running shell commands, accessing files directly, or mutating user library/project state.
- Building a frontend skill marketplace or editor in this slice.
- Letting skills bypass existing chat tool validation.

## Decisions

### Decision: Built-in declarative registry

Create a small backend module that stores skill definitions as data and exposes `list_research_skills()` / `run_research_skill()`.

Rationale: declarative definitions are easy to test, inspect, and later migrate to a database or project skill folder. This avoids embedding skill prompts directly inside `chat_agent_tools.py`.

### Decision: LLM-generated guidance, not autonomous sub-agent execution

`run_skill` will call the existing LLM service with a constrained prompt and bounded token limit, then package the output as a tool observation.

Rationale: the current agent runtime can already orchestrate tools. A nested autonomous agent would add complexity before we have a UI for inspecting nested plans.

### Decision: Read-only by construction

Skill definitions can include "allowed_tool_hints" for future planner routing, but the first `run_skill` executor will not call mutation tools or perform persistence.

Rationale: side effects already have confirmation gates at the top-level tool runtime. Skill execution should not create a hidden path around those gates.

### Decision: Deterministic fallback can route explicit skill prompts

The existing deterministic fallback can recognize direct prompts like "用 experiment-planner skill..." and emit `run_skill`.

Rationale: force mode and planner failure should still handle obvious user intent without requiring a successful planner LLM call.

## Risks / Trade-offs

- **Skill output quality depends on the active model** -> Keep prompts structured and include evaluation criteria in the observation for the final answer.
- **Users may expect skills to call other tools internally** -> Label this slice as built-in guidance execution; future changes can add multi-tool skill plans.
- **Skill registry may duplicate future toolbox data** -> Keep the registry declarative and small so it can be migrated.
- **Planner may overuse `run_skill`** -> The tool remains read-only and bounded, and the final answer still receives ordinary retrieval/tool context.
