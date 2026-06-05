## Why

Several implemented workflows currently fail at runtime despite appearing available in the UI. Core reliability must be restored before adding authorization, retrieval improvements, or layout changes so later work is built on verifiable behavior.

## What Changes

- Fix non-streaming LLM calls so successful completions return their content and usage tracking executes.
- Fix research Idea generation so paper-selection results are unpacked consistently through prompt construction and reference storage.
- Restore access to fixed paper export routes that are currently shadowed by dynamic paper detail routes.
- Correct the paper detail share action so it no longer calls the research-project sharing endpoint with a paper ID.
- Remove the duplicate profile update route registration while preserving display-name updates.
- Add focused regression tests for the repaired backend behavior and a frontend build verification step.

## Capabilities

### New Capabilities
- `core-workflow-reliability`: Core LLM, research Idea generation, paper export, profile update, and paper-detail action workflows behave consistently and remain covered by regression checks.

### Modified Capabilities

## Impact

- Backend services: `backend/app/services/llm.py`, `backend/app/services/research_service.py`
- Backend APIs: `backend/app/api/papers.py`, `backend/app/api/settings.py`
- Frontend paper detail UI: `frontend/src/pages/PaperDetailPage.tsx`
- Verification: focused backend tests and frontend production build
