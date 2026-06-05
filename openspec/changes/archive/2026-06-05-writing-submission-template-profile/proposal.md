# Change: Writing Submission Template Profile

## Why

Writing projects now distinguish structure templates from official submission templates, but users still need a concrete way to attach a venue target and inspect an uploaded template. Conference formats can change every year, so the system should bind user-provided/official template evidence to a writing project instead of relying on static built-in assumptions.

## What Changes

- Add LaTeX submission template inspection for `.tex`, `.cls`, `.sty`, and `.zip` uploads.
- Add a project-level endpoint that binds a target venue/year and inspected template metadata into the writing project profile.
- Surface the submission profile in the writing workbench export panel.
- Keep export behavior conservative: the UI explains that imported templates guide readiness and future formatting, while current export remains the existing generated package.

## Non-goals

- Do not build a full Overleaf file tree editor.
- Do not permanently store uploaded template file contents in this first slice.
- Do not claim imported templates can automatically guarantee venue compliance.

## Impact

- Backend: LaTeX template inspector and writing project profile endpoint.
- Frontend: submission profile panel and upload flow.
- Tests: service-level template inspection and profile binding regression coverage.
