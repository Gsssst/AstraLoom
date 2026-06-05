# Design: Writing Workbench Redesign

## External Patterns

Observed open-source patterns worth borrowing:

- Overleaf-style workflow: a document project is the center; templates are attached to a project, not exposed as one-off buttons.
- LaTeX checking tools such as TexGuardian/PaperDebugger: submission readiness is a checklist/diagnostic step, not just a download button.
- Research workflow agents such as ResearchClaw: writing should connect literature, project state, and external writing environment rather than only generate text.

## Architecture

The redesigned writing page has two top-level modes:

1. Paper Writing
   - Project list and create flow are always visible.
   - Selecting a project opens a workbench:
     - manuscript overview
     - section editor
     - evidence cards
     - citation coverage and sentence checks
     - Related Work/table generation
     - export readiness and package
     - conference/profile guidance

2. Grant / Proposal
   - Keeps current grant generation, review, innovation extraction, and polish tools.
   - Presents them as one coherent proposal assistant instead of a peer tab among paper tools.

## Template Model

The UI SHALL distinguish:

- `structure_template`: predefined section skeleton such as blank, survey, paper, grant.
- `target_profile`: intended venue/use case such as ACL, CVPR, NeurIPS, NSFC.
- `submission_template`: imported official files or user-provided template source.

In this first slice, `submission_template` can be represented as guidance/status text and metadata, while actual upload/parsing can be introduced in a follow-up change.

## First Slice

The first implementation focuses on:

- Make paper projects the default writing surface.
- Split paper vs grant modes.
- Move one-off paper tools into contextual action cards.
- Clarify built-in templates are structure templates and official venue format needs imported template files.

## Risks

- A full rewrite could break existing writing capabilities. Mitigation: reuse existing handlers and components.
- Users may still need one-off tools. Mitigation: keep quick action cards in the paper assistant instead of deleting them.
- Conference profile may be mistaken as official formatting. Mitigation: explicit copy in UI.
