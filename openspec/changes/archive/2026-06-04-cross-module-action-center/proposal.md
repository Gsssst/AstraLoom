# Change: Cross-module action center

## Why

Recent work has improved papers, paper QA, writing, research ideas, and project spaces independently. Users now need a balanced way to see "what should I do next" across the whole research workflow instead of visiting every module to discover maintenance gaps, unread papers, stalled ideas, or draft work.

## What Changes

- Add a read-only action center API that summarizes actionable next steps across papers, digests, research projects, writing projects, and project spaces.
- Add a frontend action center page with grouped action cards, priority/status tags, and links back to the relevant module.
- Add a sidebar entry so users can reach the cross-module workflow surface directly.

## Non-goals

- Do not add persistent task assignment, due dates, or Kanban state in this change.
- Do not replace existing module-specific actions.
- Do not introduce new database tables unless a later persistent-task iteration is approved.

## Impact

- Backend: new workflow/action summary endpoint and service.
- Frontend: new page and layout navigation entry.
- Tests: route authentication and service-level regression coverage.
