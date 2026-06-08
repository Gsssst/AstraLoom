## Why

Uploading and binding a submission template can fail with SQLAlchemy `MissingGreenlet` after the project metadata update. The update path serializes `project.sections` after commit/refresh without eager-loading the relationship, causing async lazy loading outside the expected greenlet context.

## What Changes

- Fix writing project updates so returned project data can include sections without triggering async lazy loads.
- Preserve submission template binding behavior and response shape.
- Add a regression test for update serialization with eager-loaded sections.

## Capabilities

### New Capabilities

### Modified Capabilities
- `writing-submission-template-profile`: binding a template profile must complete without backend lazy-load failures and return a usable updated project.

## Impact

- Backend service: `WritingProjectService.update_project`.
- Backend tests: focused writing closed-loop regression.
- No database migration or frontend API change.
