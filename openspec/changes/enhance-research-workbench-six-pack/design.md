## Context

The six requested improvements map cleanly to patterns in mature research tooling:
- PaperQA emphasizes answers grounded in retrieved evidence and citations.
- GROBID extracts structured scholarly metadata and references from PDFs.
- Overleaf organizes manuscripts as projects with source files, references, assets, and build logs.
- STORM turns research into a process: knowledge curation, perspective/question discovery, outline planning, and grounded drafting.
- JabRef focuses on citation keys, BibTeX quality, duplicate hygiene, and metadata completeness.
- Logseq-style knowledge tools make backlinks and graph navigation visible.

The first implementation should make those patterns usable inside the current UI without blocking on new services. That means deriving panels from existing paper/chat/project state, surfacing readiness and next actions, and leaving future backend extraction/indexing as explicit follow-up work.

## Goals / Non-Goals

**Goals:**
- Provide visible entry points for all six workflows in their natural pages.
- Use deterministic client-side summaries where backend data already exists.
- Keep existing APIs intact and avoid migrations.
- Make panels compact enough not to crowd the already-dense workbench pages.
- Add contract tests to keep the new workflow anchors from disappearing.

**Non-Goals:**
- Full GROBID server integration.
- Persistent graph database.
- Real-time collaborative LaTeX editing.
- A full STORM agent pipeline replacement for the existing idea generator.

## Decisions

- Keep all six as first-version UI/workflow panels.
  - Rationale: the app already has most source data, and the user asked for broad optimization now. This gives useful surface area quickly while preserving backend stability.
- Compute evidence confidence from existing answer metadata and references.
  - Rationale: paper chat already returns `evidence` and `references`; no new retrieval endpoint is required.
- Represent citation networks with current paper, related papers, metadata readiness, and future extraction state.
  - Rationale: actual bibliography extraction can be added later without changing the panel contract.
- Model Overleaf-style writing structure as a file tree over existing sections and exports.
  - Rationale: writing projects already store sections, evidence cards, BibTeX, and preview diagnostics.
- Add STORM process visibility around the existing research run stages.
  - Rationale: current generation pipeline already has evidence/gap/candidate/review/proposal stages; the panel reframes those as a research method.
- Use lightweight graph panels with cards/tags rather than a canvas graph.
  - Rationale: fewer layout risks, better mobile behavior, and easier tests.

## Risks / Trade-offs

- Broad UI additions can clutter pages -> place panels in existing sidebars or compact cards and use collapsible/grid layouts where possible.
- Client-derived quality scores can be mistaken for authoritative extraction -> label them as readiness/quality signals, not final truth.
- Repeated logic across pages can drift -> centralize shared graph/workflow UI where the shape is stable.
