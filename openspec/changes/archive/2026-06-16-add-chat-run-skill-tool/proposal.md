## Why

The chat tool runtime can now search papers, read local evidence, import papers, and extract Office files, but it still lacks a reusable skill layer for common research workflows. Adding `run_skill` gives the agent a controlled way to invoke repeatable research methods before the full Skill system UI exists.

## What Changes

- Add a small built-in research skill registry for common workflows such as paper scouting, method comparison, experiment planning, survey drafting, figure interpretation, and rebuttal help.
- Register a read-only `run_skill` chat tool that accepts a skill id, user task, optional context, and bounded output length.
- Return structured skill observations including selected skill metadata, expected output format, evaluation criteria, and generated guidance.
- Make the LLM planner aware of `run_skill` through the normal tool schema prompt.
- Keep this slice side-effect free: no dynamic skill installation, no filesystem plugin execution, and no mutation of library/project state.

## Capabilities

### New Capabilities

### Modified Capabilities

- `chat-agent-tool-runtime`: The registered tool set expands with read-only `run_skill` execution for built-in research skills.
- `research-toolbox`: Built-in research skills become inspectable/callable toolbox assets exposed through the chat runtime contract.

## Impact

- Backend skill registry/service under `backend/app/services/`.
- Chat tool registry in `backend/app/services/chat_agent_tools.py`.
- Planner visibility via existing registry schema flow.
- Focused backend tests for skill listing, execution, invalid skill rejection, read-only policy, and deterministic/planner visibility.
