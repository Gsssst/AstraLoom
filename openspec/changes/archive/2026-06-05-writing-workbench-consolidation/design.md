## Overview

This change consolidates the writing assistant around a project-first workbench. It does not remove existing writing tools. Instead, it adds a project summary layer that turns existing signals into visible workflow guidance.

## External Inspiration

- Template-aware academic writing assistants such as TexGuardian emphasize that venue formatting must be verified against the official template instead of hard-coded.
- Citation-checking projects such as RefChecker emphasize that references should be validated and not treated as text decorations.
- Paper writing workflows such as vibe-paper-writing and ResearchPilot organize notes, evidence, feedback, and Related Work into a visible pipeline.

The implementation borrows the workflow shape, not their code: project status first, evidence/citation risk visible, then clear next actions.

## Backend

`WritingProjectService.build_workbench_summary(project_id, user_id)` will compose existing project data:

- project metadata and progress
- evidence coverage from `get_evidence_cards`
- export/template readiness from `build_export_readiness`
- section risks from empty/short sections
- citation risks from readiness summary
- recommended next actions

The endpoint returns deterministic JSON so the frontend can render without running an LLM.

## Frontend

`WritingPage` will fetch the workbench summary whenever a project is selected or sections change. The project tab will show a compact summary card above the editor:

- workflow stage
- progress / words / evidence / citation stats
- target venue/template status
- warnings
- next-action buttons

Existing panels remain available:

- section editor
- evidence cards
- publication export package
- one-off citation, Related Work, polish, abstract, literature review, compare tools

## Tradeoffs

- The summary is rule-based rather than AI-generated so it is stable and fast.
- First version focuses on paper-writing projects. Grant/proposal mode remains separate and can receive a similar workbench later.
