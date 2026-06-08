## Context

The existing bridge can create a Writing project from a Research Idea, preserving source Idea metadata and evidence items. That is useful, but it produces sections directly from the Idea and evidence table. After recent Proposal workflow improvements, richer upstream signals now exist: validation readiness, experiment execution packs, structured review packages, revision provenance, and version history. The bridge should use those signals to produce a writing-preparation artifact before creating a draft.

Comparable open-source research-writing tools point toward a staged flow rather than immediate long-form generation:
- STORM separates pre-writing research/outline/reference organization from the final writing stage.
- ScholarCopilot-style tools emphasize citation-aware academic writing and reducing unsupported citation use.
- AutoResearchClaw-style systems include heavier end-to-end research/writing, but the safer local fit is a bounded brief that the user can inspect and edit before drafting.

## Goals / Non-Goals

**Goals:**
- Build a bounded Proposal writing brief from existing Proposal lifecycle data.
- Let users preview the brief before creating a Writing project.
- Persist the brief in Writing project metadata.
- Use the brief to seed Writing sections more specifically than the current direct conversion.
- Explicitly distinguish supported claims from unsupported/unsafe claims.

**Non-Goals:**
- Full long-form paper generation.
- New relational tables for briefs or claim graphs.
- Automatic BibTeX verification beyond preserving existing local/external evidence metadata.
- Multi-agent writing or external search expansion during brief creation.

## Decisions

### Store writing brief in existing JSON metadata

The brief will be stored in two places:
- Returned by `GET /api/research/ideas/{idea_id}/writing-brief` for preview.
- Embedded into Writing project `metadata_json["writing_brief"]` when `POST /api/research/ideas/{idea_id}/writing-draft` creates a project.

This avoids migrations and matches existing metadata-driven writing context patterns.

### Use deterministic fallback as the core contract

The writing brief structure should be stable even when the LLM is unavailable. The fallback derives:
- title candidates from Proposal title and research project name
- abstract draft from hypothesis, approach, and experiment plan
- contribution chain from novelty, review package, and scores
- section outline from standard paper sections and available project sections
- claim-evidence map from evidence items and Proposal claims
- unsafe claims from validation/review blockers and missing evidence

An LLM can improve wording later, but the endpoint must remain usable without model output.

### Keep claims conservative

The brief must not invent citations. Evidence references come only from `idea.evidence_json.items`, `referenced_papers`, and local imported paper IDs. If a claim lacks supporting evidence, the brief marks it under `unsafe_claims` instead of presenting it as ready-to-write.

### Reuse the existing draft endpoint

The existing draft endpoint remains the main "create writing project" action. It will call the same brief builder internally and seed sections from the brief, so users who skip preview still get the improved scaffold.

## Risks / Trade-offs

- [Risk] The brief becomes too verbose for the Proposal page. -> Render it as a compact panel with collapsible/detail blocks and bounded list lengths.
- [Risk] Users treat fallback wording as final prose. -> Label unsupported claims and evidence status clearly; seed drafts as scaffolds, not final text.
- [Risk] Metadata grows too large. -> Bound lists and store concise brief fields rather than raw prompts or full paper text.
- [Risk] LLM output overclaims. -> Normalize against existing evidence and preserve unsupported claims separately.
