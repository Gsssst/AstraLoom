## Why

Deleting a research direction currently fails when the project has persisted Idea Workbench runs. SQLAlchemy attempts to null `research_idea_runs.project_id`, but that column is non-nullable, so users see a generic deletion failure even though they own the project.

## What Changes

- Ensure deleting an owned research project also removes its associated ideas and Idea Workbench runs.
- Keep the existing owner-only deletion authorization boundary unchanged.
- Improve the research direction delete error path so frontend users see backend details when available.

## Capabilities

### New Capabilities

### Modified Capabilities
- `research-idea-workbench`: Project deletion must clean up persisted workbench run state and selected proposals without failing on non-null child foreign keys.

## Impact

- Backend ORM relationship configuration in `backend/app/db/models/research.py`.
- Research project deletion endpoint behavior in `backend/app/api/research.py`.
- Frontend delete feedback in `frontend/src/pages/ResearchPage.tsx`.
- Backend regression coverage for deleting projects with runs and ideas.
