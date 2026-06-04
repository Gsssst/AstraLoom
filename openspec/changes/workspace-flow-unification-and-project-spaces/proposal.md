# workspace-flow-unification-and-project-spaces

## Why

The product has strong individual modules (chat, papers, research ideas, writing), but users still experience them as separate tools. There is no shared project space that groups papers, research directions, writing drafts, and collaborators around one research effort. This weakens workflow continuity and blocks the multi-user/project-space roadmap.

## What Changes

- Add project spaces as a shared container for papers, research projects, and writing projects.
- Add basic project-space membership with owner/editor/viewer roles.
- Add a unified workspace page that summarizes recent papers, research directions, writing drafts, next actions, and members.
- Add sidebar navigation to the workspace page.
- Add lightweight startup table creation for new workspace tables in development.

## Non-Goals

- Real-time collaborative editing.
- Fine-grained per-section permissions.
- Cross-user chat sharing.
- Full migration framework overhaul.

## Reference Patterns

- Open-source reference managers and research workbenches commonly organize work around collections/projects before exposing papers and notes.
- Collaborative workspace products separate resource ownership from membership, then use role checks for write operations.

## Success Criteria

- Authenticated users can create, list, view, update, and delete their own project spaces.
- Project-space owners can add/remove members by username or email.
- Project spaces summarize linked/recent paper, research, and writing resources.
- The frontend exposes a unified "项目空间" entry and detail page.
- Existing module tests and frontend build still pass.
