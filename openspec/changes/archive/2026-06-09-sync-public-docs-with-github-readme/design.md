## Context

The README has been rewritten as a concise GitHub-facing homepage for AstraLoom. The repository also includes deeper Markdown documents that serve different readers:

- `introduction.md`: product and system overview.
- `user-manual.md`: operational guide for lab admins and lab members.
- `frontend/README.md`: frontend contributor notes.
- `openspec/project.md`: OpenSpec project context used during future changes.

These files should agree on product identity and positioning while avoiding duplicated long README content.

## Decisions

- Treat `README.md` as the short public entry point.
- Treat `introduction.md` as the deeper architecture and module overview.
- Treat `user-manual.md` as the workflow-oriented operating manual.
- Replace default template wording in `frontend/README.md` because it is misleading once the repo is on GitHub.
- Keep safety guidance concise in the README, but include fuller data-boundary guidance in the manual and introduction.

## Non-Goals

- No frontend UI changes.
- No backend behavior changes.
- No new features, migrations, or dependencies.
- No long GitHub upload checklist in the README.

## Validation

- Run OpenSpec validation for this change.
- Run strict spec validation.
- Run Markdown/link-oriented sanity checks with `rg`.
- Run `git diff --check`.
