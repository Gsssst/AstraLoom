## Why

The writing page already has project summaries, evidence cards, citation checks, and export tools, but the selected-project surface still feels like a collection of panels rather than a clear writing workflow. Users need a compact way to see current stage, risk, blocking issues, and the next action before editing sections.

## What Changes

- Add a compact stage and readiness strip for the selected writing project.
- Make recommended next actions more scannable with priority, target area, and one-click navigation.
- Surface project blockers such as empty sections, short sections, evidence gaps, citation risks, and missing official templates as structured chips.
- Keep existing section editing, evidence cards, citation checks, quality checks, pipeline actions, and export controls unchanged.

## Capabilities

### New Capabilities

### Modified Capabilities
- `writing-workbench-consolidation`: The workbench summary UI must expose stage, risk, blockers, and next actions in a compact action-first workflow before section editing.

## Impact

- Frontend writing project workbench in `frontend/src/pages/WritingPage.tsx`.
- Frontend writing workbench contract tests.
- No backend API, database, or dependency changes.
