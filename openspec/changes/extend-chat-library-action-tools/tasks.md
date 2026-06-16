## 1. Backend Tool Runtime

- [x] 1.1 Add typed argument schemas for `read_pdf`, `add_to_folder`, and `create_research_project`.
- [x] 1.2 Implement `read_pdf` as a bounded read-only local-paper evidence tool using full text chunks when available and abstract fallback otherwise.
- [x] 1.3 Implement `add_to_folder` as a confirmed side-effect tool that validates folder and local paper IDs for the current user.
- [x] 1.4 Implement `create_research_project` as a confirmed side-effect tool that creates a project for the current user and links valid local papers.
- [x] 1.5 Register the new tools in `default_chat_tool_registry` with correct side-effect flags.
- [x] 1.6 Extend deterministic tool routing for obvious local PDF reading, folder add, and research project creation prompts.

## 2. Chat Confirmation UX

- [x] 2.1 Update chat tool confirmation request validation to accept the new side-effect tool names.
- [x] 2.2 Generalize frontend trace confirmation handling so waiting-confirmation steps for `add_to_folder` and `create_research_project` render safe action labels.
- [x] 2.3 Preserve existing `import_paper` confirmation behavior and Research Scout card actions.

## 3. Verification

- [x] 3.1 Add backend runtime tests for tool registration, `read_pdf` full-text/abstract behavior, and invalid local paper access.
- [x] 3.2 Add backend side-effect tests for confirmation gating and confirmed `add_to_folder` / `create_research_project` execution.
- [x] 3.3 Add planner/fallback tests that expanded tool schemas reach the planner and deterministic routing can create obvious tool calls.
- [x] 3.4 Update frontend contract tests for expanded side-effect confirmation buttons and labels.
- [x] 3.5 Run OpenSpec validation, focused backend tests, frontend contract tests, and frontend build.
