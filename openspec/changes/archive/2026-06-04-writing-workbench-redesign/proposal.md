# Change: Writing Workbench Redesign

## Why

The writing assistant has accumulated useful features, but the current UI presents them as scattered tools: citation recommendation, Related Work, polishing, abstract generation, literature review, grant writing, and project management are separate tabs. This makes paper writing feel like a collection of utilities instead of a complete manuscript workflow.

Conference export is also too optimistic. Conference formats change across years, so the system should not pretend a static built-in "CVPR/ACL/NeurIPS" section template is an official submission format. Users should be able to select a writing target and, for submission formatting, import or attach an official template.

## What Changes

- Reframe the writing page around two assistants:
  - Paper writing assistant: manuscript projects, sections, evidence, citations, Related Work, export readiness, and conference profile.
  - Grant/proposal writing assistant: proposal sections, review, innovation extraction, and polishing.
- Make project management the primary paper-writing surface instead of a hidden tab.
- Keep existing one-off tools, but expose them as contextual actions within the relevant assistant.
- Add a template/profile model in the UI vocabulary that distinguishes:
  - structure template: project section layout
  - submission template: user-imported or official conference formatting source
- Prepare for future template import and conference-specific writing guidance.

## Non-goals

- Do not remove existing writing APIs in this change.
- Do not claim static built-in templates are official current-year conference formats.
- Do not implement a full Overleaf-like editor in the first slice.
- Do not add paid external integrations.

## Impact

- Frontend: major `WritingPage` information architecture change.
- Frontend components: project panel wording and creation flow become writing-target aware.
- Backend/OpenSpec: document the distinction between section templates and submission templates.
- Future backend: template upload/profile persistence can be added after the UI/workflow is validated.
