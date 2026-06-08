## Context

The research-to-writing bridge persists `writing_brief`, `claim_evidence_map`, `unsafe_claims`, evidence items, and source Idea metadata in `WritingProject.metadata_json`. The Writing workbench already has a project-first layout with sections, evidence cards, citation checks, quality checks, and export readiness, but it does not render the Proposal brief.

GitHub/project research pointed to three useful patterns:
- ScholarCopilot-like writing assistants keep citation/evidence suggestions close to the active writing context.
- RefChecker-like systems treat generated claims as units that must be marked supported, partially supported, or unsupported.
- Research workflow assistants keep project state persistent rather than treating generation outputs as one-off text.

This change therefore makes the existing Proposal brief a first-class workbench panel and a source of lightweight blockers, without introducing another LLM review loop.

## Goals / Non-Goals

**Goals:**
- Render the preserved writing brief in the Writing workbench for research-derived projects.
- Make unsafe claims and evidence gaps visible before users polish or export draft text.
- Keep the interaction lightweight: copy, jump, inspect, and reuse existing evidence/citation tools.
- Use existing metadata and frontend state; avoid a migration.

**Non-Goals:**
- Do not add a full automatic fact-checking pipeline.
- Do not change how writing briefs are generated.
- Do not add new provider/model dependencies.
- Do not alter `.env` or API credentials.

## Decisions

1. **Read from `selectedProject.metadata_json.writing_brief` first.**
   - Rationale: the previous bridge already persists the bounded brief. Re-fetching through research endpoints would add coupling and access edge cases.
   - Alternative considered: add a new `/writing/projects/{id}/writing-brief` endpoint. This is unnecessary until the backend needs to normalize or recompute the brief.

2. **Add a compact workbench panel instead of another tab.**
   - Rationale: the brief is project context, not a standalone tool. It should appear near sections/evidence for research-derived drafts.
   - Alternative considered: place it in the existing evidence sidebar only. That would hide title/outline/contribution information and make the sidebar too dense.

3. **Use lightweight client-derived risk summaries.**
   - Rationale: unsafe claims and unsupported claim counts can be computed from existing metadata and shown immediately.
   - Alternative considered: run LLM checks on each render. This would be slow, costly, and outside the current scope.

4. **Integrate with existing navigation targets.**
   - Rationale: the workbench already routes users to sections, evidence, citations, and export. Writing-brief actions should reuse that mental model.

## Risks / Trade-offs

- Brief metadata may be absent on older writing projects -> show nothing and keep the workbench usable.
- Claim/evidence status can be stale if the user later adds evidence manually -> label the panel as Proposal writing guidance and keep citation checks as the stronger section-level validation.
- A large brief could crowd the page -> render bounded lists and use collapsible panels.
