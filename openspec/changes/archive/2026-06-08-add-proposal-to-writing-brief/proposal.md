## Why

Research Proposal iteration is now fairly mature, but the handoff into Writing still jumps from "idea" to "draft" too quickly. Users need a writing-preparation layer that turns a reviewed Proposal into a structured, evidence-bound brief before creating a writing project, so early paper drafts do not overclaim or lose citation context.

## What Changes

- Add a deterministic Proposal writing brief generated from Proposal fields, evidence, validation, execution pack, review package, experiment plan, and revision provenance.
- Add an owner-scoped API endpoint to preview or refresh the writing brief before creating a Writing project.
- Persist the writing brief into the Writing project metadata when creating a draft from a Proposal.
- Improve the generated Writing project sections using the brief: title candidates, abstract, contribution chain, section outline, claim-evidence map, Related Work comparison notes, experiment writing plan, limitations, and unsafe claims.
- Surface the writing brief in the Research Project Proposal detail UI before the existing "generate writing draft" action.
- Keep citation grounding conservative: the brief may only reference existing Proposal evidence items and must mark unsupported claims instead of inventing citations.

## Capabilities

### New Capabilities

### Modified Capabilities

- `research-to-writing-evidence-bridge`: enhance the Proposal-to-Writing bridge with previewable writing briefs, claim-evidence constraints, and brief-aware Writing project creation.

## Impact

- Backend: Research API, WritingProjectService, ResearchIdeaWorkbenchService or adjacent helper methods, tests.
- Frontend: ResearchProjectPage Proposal detail panel, loading/error state, create draft messaging, contract tests.
- Persistence: existing Writing project `metadata_json`; no new database table expected.
- AI behavior: optional LLM-generated brief with deterministic fallback; no direct long-form paper generation in this change.
