## 1. OpenSpec And Contract Setup

- [x] 1.1 Validate the OpenSpec change before implementation.
- [x] 1.2 Extend page-shell contract tests for Papers, Research, ResearchProject, and Writing page shell adoption.

## 2. Primary Workflow Shell Adoption

- [x] 2.1 Apply `PageShell` to `ResearchPage` and move create-direction into shell actions.
- [x] 2.2 Apply `PageShell` to `PapersPage` and move high-level paper actions into shell actions while preserving search/filter controls.
- [x] 2.3 Apply `PageShell` to `ResearchProjectPage` and move back/generate commands into shell actions while preserving workbench tabs.
- [x] 2.4 Apply `PageShell` to `WritingPage` and move assistant mode control into shell actions while preserving writing tabs and tools.

## 3. Visual Cleanup

- [x] 3.1 Remove bespoke gradient hero wrappers from the four primary workflow pages.
- [x] 3.2 Keep dense body controls stable and prevent title/action duplication after shell adoption.

## 4. Verification

- [x] 4.1 Run OpenSpec strict validation after implementation.
- [x] 4.2 Run targeted frontend contract tests.
- [x] 4.3 Run frontend build and `git diff --check`.
