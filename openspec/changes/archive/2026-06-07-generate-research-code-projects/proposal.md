## Why

The current Research Idea code generation produces a single code string, which is too weak for a paper idea that needs datasets, baselines, method code, ablations, analysis, and reproducible run instructions. Similar automated research systems such as AI-Scientist and CodeScientist organize output around experiment project folders, templates, logs, reports, and runnable scripts rather than one pasted file.

## What Changes

- Replace the user-facing "generate code" experience with generation of a structured experiment project package for each Proposal.
- Store a project manifest containing multiple files, framework, entrypoints, setup instructions, run commands, and safety notes.
- Add an API to download the generated project package as a zip archive.
- Update the Research Project page to show a file tree, file preview, package metadata, and download action.
- Keep the existing `generated_code` field as backward-compatible legacy output, but stop treating it as the primary experience.

## Capabilities

### New Capabilities
- `research-code-project-generation`: Research Ideas can generate, inspect, and download a structured experiment project package.

### Modified Capabilities

## Impact

- Affects `backend/app/services/research_service.py`, `backend/app/api/research.py`, `backend/app/db/models/research.py`, Alembic migrations, `frontend/src/pages/ResearchProjectPage.tsx`, and focused backend/frontend tests.
- Adds no runtime code execution of generated projects; generated code is treated as an artifact for user review/download.
- Requires a database migration to persist structured project metadata on `research_ideas`.
