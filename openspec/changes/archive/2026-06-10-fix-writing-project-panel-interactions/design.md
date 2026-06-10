## Context

The writing project panel renders each project as a clickable Card and renders the delete action in the Card `extra` area. Without stopping propagation, delete clicks can also trigger project selection. The parent page owns `selectedProject` and many dependent state slices; deleting the selected project without clearing those slices leaves the page rendering stale project data.

## Decisions

- Add an optional `onProjectDeleted` callback to `WritingProjectPanel`.
- Stop propagation on delete controls and popconfirm actions.
- Add a `clearSelectedProject` helper in `WritingPage`.
- Make `handleSelectProject` normalize section and metadata fields before writing them into state.
- Surface create/delete errors instead of silently ignoring them.

## Non-Goals

- Redesigning the writing panel UI.
- Changing backend delete behavior.
- Adding bulk cleanup for duplicate projects.
