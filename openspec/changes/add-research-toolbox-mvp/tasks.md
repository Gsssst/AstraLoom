## 1. Data Model and Migration

- [x] 1.1 Add toolbox models and relationships for tools and paper links.
- [x] 1.2 Add Alembic migration with indexes for kind, maturity, tags/search, and paper links.

## 2. Backend APIs

- [x] 2.1 Add toolbox CRUD/list endpoints.
- [x] 2.2 Add endpoints for linking/unlinking papers to toolbox entries.
- [x] 2.3 Add paper-linked toolbox retrieval endpoint.
- [x] 2.4 Add selected toolbox context to idea-run request models and run config.
- [x] 2.5 Load selected toolbox context into candidate generation prompts and persisted candidate metadata.

## 3. Frontend Toolbox Experience

- [x] 3.1 Add Toolbox navigation route and lazy page.
- [x] 3.2 Build toolbox list, filters, and create/edit drawer.
- [x] 3.3 Show linked paper evidence inside toolbox details.
- [x] 3.4 Add paper detail action for linking or creating a toolbox entry from a paper.
- [x] 3.5 Add toolbox selector and mode controls to research idea generation.

## 4. Verification

- [x] 4.1 Add backend tests for CRUD, paper links, and idea-run toolbox context.
- [x] 4.2 Add frontend contract tests for route, page controls, paper link action, and idea-run payload.
- [x] 4.3 Run backend tests, frontend tests/build, and OpenSpec validation.
- [ ] 4.4 Commit implementation and archive the OpenSpec change.
