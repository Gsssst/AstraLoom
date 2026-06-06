## 1. Backend Deletion Semantics

- [x] 1.1 Align research ORM relationships with database cascade behavior for projects, workbench runs, and idea lineage.
- [x] 1.2 Verify the delete endpoint keeps owner-only access while deleting projects with associated runs and ideas.

## 2. User Feedback

- [x] 2.1 Surface backend delete error details in the research direction list when available.

## 3. Verification

- [x] 3.1 Add regression coverage for deleting an owned research project with an Idea Workbench run and generated idea.
- [x] 3.2 Run the targeted backend/frontend checks for the touched behavior.
