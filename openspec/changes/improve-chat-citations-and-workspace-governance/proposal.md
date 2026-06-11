## Why

The chat UI can show web references that are unrelated to the assistant answer, which makes citations look untrustworthy. The current implementation returns all web retrieval results as assistant references before the model has answered, even when fallback search providers return low-signal pages for an accidental or poor query.

Admin governance also stops at workspace ownership and member counts. Administrators need a way to inspect a project space's actual resources, members, issues, activity, and assistant context for operational support. Workspace owners currently add members by typing a username or email from memory, which is fragile for small lab deployments where users may not know exact account identifiers.

## What Changes

- Filter web search references by lexical relevance to the original chat query before injecting them into chat context or returning them as references.
- Include retrieval metadata on web references so users can see which query produced a source.
- Adjust chat reference copy so the UI distinguishes retrieved sources from verified answer citations.
- Add an admin-only workspace detail endpoint that returns the same rich workspace content administrators need for inspection without requiring workspace membership.
- Add admin console actions to open a workspace's content.
- Add a workspace member candidate endpoint and replace the raw member account input with a searchable user picker while preserving typed username/email compatibility.

## Prior Art

- GitHub research: Plane (`makeplane/plane`) separates an admin app from the space app and models collaborative workspaces as first-class inspectable entities. Its issue/member property surfaces use selectable user/member controls rather than relying on remembered free-text account identifiers.
- Product takeaway for AstraLoom: keep administrator inspection explicit and admin-only, and use searchable in-app user selection for member management.

## Capabilities

### New Capabilities
- `workspace-member-picker`: Workspace owners can search/select eligible users when adding members.

### Modified Capabilities
- `chat-web-research`: Web references shown with chat answers are filtered for query relevance and expose retrieval-query metadata.
- `admin-workspace-governance`: Administrators can inspect project-space contents, not only ownership and counts.
- `workspace-flow-unification-and-project-spaces`: Workspace member management supports selectable users in addition to typed account identifiers.

## Impact

- Backend:
  - `backend/app/services/web_search.py`
  - `backend/app/api/workspaces.py`
  - `backend/app/services/workspace_service.py`
  - `backend/app/api/admin.py`
  - targeted tests for retrieval filtering, admin workspace detail, and member candidates
- Frontend:
  - `frontend/src/pages/ChatPage.tsx`
  - `frontend/src/pages/AdminPage.tsx`
  - `frontend/src/pages/WorkspaceDetailPage.tsx`
- No database migration expected.
