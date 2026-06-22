## 1. Persistence

- [x] 1.1 Add nullable user LLM provider/model fields to the ORM model.
- [x] 1.2 Add an Alembic migration for existing users.

## 2. Backend Behavior

- [x] 2.1 Add request-context model preference resolution to the LLM service.
- [x] 2.2 Set LLM request preference from authenticated user dependencies.
- [x] 2.3 Change settings API read/save/test behavior to user-scoped preferences.

## 3. Frontend Settings

- [x] 3.1 Update the API settings tab copy and status fields for user-scoped model selection.
- [x] 3.2 Allow non-admin authenticated users to save and test configured model options.

## 4. Verification

- [x] 4.1 Add backend tests for per-user preference persistence and LLM resolution.
- [x] 4.2 Add frontend contract coverage for user-scoped API settings UI.
- [x] 4.3 Run OpenSpec validation, focused tests, and frontend build.
