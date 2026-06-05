## 1. Persisted Workbench Runs

- [x] 1.1 Add the `ResearchIdeaRun` model and enriched structured metadata fields on `ResearchIdea`
- [x] 1.2 Add an Alembic migration for workbench runs and enriched proposal fields

## 2. Independent Workbench Pipeline

- [x] 2.1 Implement a standalone `ResearchIdeaWorkbenchService` with persisted stage transitions
- [x] 2.2 Build local Evidence Map collection with seed, background, and inspiration categories
- [x] 2.3 Add structured Gap Map extraction, multi-path candidate generation, deduplication, explainable review, and top-proposal persistence

## 3. Workbench API

- [x] 3.1 Add request and response schemas for runs, artifacts, reviewed candidates, and enriched proposals
- [x] 3.2 Add project-owned run creation, run-detail, latest-run, and SSE progress endpoints
- [x] 3.3 Preserve compatibility by routing the existing idea-generation endpoint through the new workbench pipeline

## 4. Research Project Interface

- [x] 4.1 Replace the opaque generation action with a Research Idea Workbench stage panel
- [x] 4.2 Add inspectable Evidence Map, Gap Map, candidate pool, and selected-proposal views
- [x] 4.3 Display proposal review dimensions, rationale, evidence references, and minimum experiment plan while preserving discussion and code-generation actions

## 5. Verification

- [x] 5.1 Add backend coverage for stage persistence, ownership boundaries, deduplication, ranking, and proposal persistence
- [x] 5.2 Run targeted backend tests, frontend production build, and OpenSpec validation
