## 1. Backend Skill Registry

- [x] 1.1 Create a declarative built-in research skill registry with stable ids and metadata.
- [x] 1.2 Add a bounded skill execution helper that builds a structured prompt and calls the existing LLM service.
- [x] 1.3 Return clear rejection metadata for unknown skill ids.

## 2. Chat Tool Runtime Integration

- [x] 2.1 Add `RunSkillArgs` and register read-only `run_skill` in the default chat tool registry.
- [x] 2.2 Package skill execution output as `ChatToolObservation` context, references, artifacts, and details.
- [x] 2.3 Add deterministic fallback routing for explicit built-in skill prompts.

## 3. Tests And Verification

- [x] 3.1 Add backend tests for built-in skill listing and declarative metadata.
- [x] 3.2 Add backend tests for successful `run_skill` execution with mocked LLM output.
- [x] 3.3 Add backend tests for unknown skill rejection and read-only schema policy.
- [x] 3.4 Add backend tests for deterministic routing of explicit skill prompts.
- [x] 3.5 Run OpenSpec validation and focused backend tests.
