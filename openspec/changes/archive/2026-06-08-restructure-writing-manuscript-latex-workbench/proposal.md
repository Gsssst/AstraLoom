## Why

The current writing page mixes manuscript writing, survey generation, one-off writing tools, and submission template setup in one tab strip. Manuscript writing should instead feel like a paper editor: users move chapter by chapter, write LaTeX source, preview/compile the result, and summon AI help for the current section.

## What Changes

- Restructure the paper writing surface into a chapter-driven manuscript workbench.
- Separate manuscript writing from survey/literature-review workflows so surveys are not the default paper-writing entry.
- De-emphasize template selection in the main manuscript workflow; template/profile setup moves to export/submission readiness.
- Treat each writing section as LaTeX source that can be edited and previewed.
- Add section-level and project-level LaTeX compile/preview checks that report errors and warnings.
- Add a current-section AI assistant panel with context-aware actions for drafting, improving, evidence insertion, claim safety, polishing, and LaTeX error repair.
- Keep existing writing project data model and endpoints compatible where practical.

## Capabilities

### New Capabilities
- `writing-manuscript-latex-workbench`: chapter-driven manuscript writing with LaTeX editing, preview checks, and section-scoped AI assistance.

### Modified Capabilities
- `writing-workbench-redesign`: paper writing, survey writing, and grant writing must be separated so manuscript writing is chapter-first rather than tool-tab-first.

## Impact

- Frontend: `WritingPage.tsx`, `SectionEditor.tsx`, writing project panel/workbench contracts.
- Backend: writing project LaTeX preview/compile helper endpoints and tests.
- OpenSpec: new manuscript LaTeX workbench spec and workbench redesign delta.
- No schema migration planned for the first version; existing `WritingSection.content` stores LaTeX body source.
- External learning: Overleaf-style editor/preview layout, TeXlyre-style local-first LaTeX editing, and AI writing assistants informed the decision to attach AI to current section context instead of exposing disconnected tool tabs.
