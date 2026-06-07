## Context

Utility pages now use `PageShell`, while primary workflow pages still maintain their own gradient hero wrappers and page-level action regions. `PapersPage`, `ResearchPage`, `ResearchProjectPage`, and `WritingPage` are dense work surfaces, so this change should improve consistency without flattening their domain-specific controls.

Comparable open-source/product patterns reviewed before implementation:
- Paperlib: keeps paper management focused on a compact library/search surface with clear actions.
- OpenPrism-style writing workbenches: favor project/editor/output panes over marketing-style hero content.
- Lumi-style research workflow surfaces: foreground stage/state and next actions rather than decorative branding.

## Goals / Non-Goals

**Goals:**
- Apply `PageShell` to the four primary workflow pages.
- Move page identity and top-level commands into shell headers.
- Keep dense controls close to their work areas.
- Remove dominant gradient hero cards from primary workflow pages.
- Add contract tests for the new page-shell expectations.

**Non-Goals:**
- Redesign backend workflows or API payloads.
- Replace existing tabs, modals, search controls, generation pipelines, or writing tools.
- Introduce new dependencies or routing changes.
- Solve chunk-size/build performance warnings.

## Decisions

- Use `PageShell` as the only new shared layout primitive.
  - Rationale: it is already established across settings, workspaces, action center, paper digests, admin, and workspace detail.
  - Alternative considered: create a separate `WorkflowPageShell`; rejected because it would duplicate layout responsibility before proving a real need.
- Keep workflow guidance and dense filters inside the body.
  - Rationale: `WorkflowStepGuide`, search filters, proposal tabs, and writing tool tabs are task-level controls, not global page navigation.
  - Alternative considered: move all controls into shell actions; rejected because actions would become crowded and less scannable.
- Remove gradient hero blocks rather than restyle them.
  - Rationale: primary app pages should feel work-focused and consistent with the rest of the authenticated product.
  - Alternative considered: keep gradient cards as section headers; rejected because the project already moved away from this pattern.
- Implement page-by-page in one change with focused contract coverage.
  - Rationale: the four pages form one primary workflow loop: papers -> research -> proposal detail -> writing.
  - Alternative considered: four separate changes; rejected because the requirement is shared and the modifications are mostly layout-level.

## Risks / Trade-offs

- [Risk] Shell actions on dense pages could become crowded.
  -> Mitigation: only move top-level commands into shell actions; leave filters and detailed workbench controls in content cards.
- [Risk] Removing hero cards may make pages feel less visually distinct.
  -> Mitigation: use domain icons, concise subtitles, workflow guides, and existing content metrics to preserve page identity.
- [Risk] Touching four large pages increases regression risk.
  -> Mitigation: avoid changing data fetching and event handlers; add contract tests; run TypeScript build.
