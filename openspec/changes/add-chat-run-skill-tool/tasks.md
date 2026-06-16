## 1. Backend Skill Registry

- [ ] 1.1 Create a declarative built-in research skill registry with stable ids and metadata.
- [ ] 1.2 Add a bounded skill execution helper that builds a structured prompt and calls the existing LLM service.
- [ ] 1.3 Return clear rejection metadata for unknown skill ids.

## 2. Chat Tool Runtime Integration

- [ ] 2.1 Add `RunSkillArgs` and register read-only `run_skill` in the default chat tool registry.
- [ ] 2.2 Package skill execution output as `ChatToolObservation` context, references, artifacts, and details.
- [ ] 2.3 Add deterministic fallback routing for explicit built-in skill prompts.

## 3. Tests And Verification

- [ ] 3.1 Add backend tests for built-in skill listing and declarative metadata.
- [ ] 3.2 Add backend tests for successful `run_skill` execution with mocked LLM output.
- [ ] 3.3 Add backend tests for unknown skill rejection and read-only schema policy.
- [ ] 3.4 Add backend tests for deterministic routing of explicit skill prompts.
- [ ] 3.5 Run OpenSpec validation and focused backend tests.
