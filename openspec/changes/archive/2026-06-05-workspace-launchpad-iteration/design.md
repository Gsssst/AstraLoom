## Context

The existing workspace implementation already has the hard pieces: authenticated spaces, members, durable resource links, candidate search, activity logs, resource backlinks, and dashboard metrics. The biggest usability gap is that the user must still infer how to progress from a space into papers, research, and writing.

## Goals / Non-Goals

**Goals:**
- Make `/workspaces` communicate each space's stage and resource coverage.
- Make `/workspaces/:id` provide a compact project launchpad with role-aware quick actions.
- Help users bind existing resources or jump to module pages with the space context visible.
- Preserve existing resource operations and permission boundaries.

**Non-Goals:**
- Add real-time collaboration.
- Add workspace-scoped creation APIs for every resource type.
- Change workspace member roles or access-control semantics.
- Rebuild the entire project-space dashboard.

## Decisions

- Use existing workspace summary/dashboard fields where possible.
  - Rationale: the backend already computes `dashboard.stage_label`, `progress_score`, `status_cards`, and linked resource counts.
  - Alternative considered: create a new launchpad endpoint. That would be cleaner long term, but it duplicates current detail data for this iteration.
- Enrich list responses with summary data.
  - Rationale: users should not need to open every space just to understand whether it has papers, directions, or writing drafts.
  - Trade-off: list responses do a little more work, but space counts are small and this is more useful than a flat list.
- Keep quick actions as navigation and local UI actions.
  - Rationale: this avoids risky API churn while still making the workflow smoother.

## Risks / Trade-offs

- [Risk] Workspace list loading becomes heavier. → Mitigation: reuse compact summaries and keep candidate/resource detail loading on the detail page.
- [Risk] Quick action labels imply automatic creation inside a space when the target module does not yet accept workspace context. → Mitigation: label them as "去创建/去绑定" and add visible guidance that resources can be bound back to the space.
- [Risk] The page becomes visually crowded. → Mitigation: keep launchpad actions to three primary steps and preserve the existing detailed resource sections below.
