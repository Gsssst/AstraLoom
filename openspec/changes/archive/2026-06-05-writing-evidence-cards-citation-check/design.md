# Design

## Data Flow

1. Writing projects already store evidence in `metadata_json`.
2. `WritingProjectService.get_evidence_cards()` normalizes this metadata into UI-ready cards.
3. `WritingProjectService.check_section_citations()` parses a section's text, maps citation markers to evidence cards, and scores support for local papers.
4. The writing project page fetches cards when a project is selected and passes citation-check actions into each `SectionEditor`.

## Evidence Card Shape

Each card contains:

- `index` and `citation_marker` for quick insertion/copy.
- `title`, `year`, `authors`, and identifier fields.
- `paper_id` when the evidence is already in the local knowledge base.
- `arxiv_id`, `doi`, or external source metadata when it is not local yet.
- `role`, `role_label`, and `snippet`.
- `local_status`: `local`, `external`, or `unknown`.

## Citation Check Strategy

The MVP keeps the algorithm deterministic and transparent:

- Parse bracket references (`[1]`), local `Paper ID: ...`, and arXiv references.
- Map bracket references to evidence card order.
- For local papers, reuse `WritingAssistantService.score_sentence_paper_match()` and `classify_citation_role()`.
- For external-only evidence, mark as `unchecked_external` instead of pretending it was verified.
- For sections with no citations, report `missing_citation` and recommend evidence cards.

## UX

The writing project tab gains a right-side evidence panel. Each section editor gains a `校验引用` action and shows a compact diagnostic summary after checking. The UI emphasizes actionable next steps: copy citation marker, import/check local evidence, or revise unsupported sentences.

## Risks

- Metadata from old projects can be sparse. The service must degrade gracefully and show "证据不足" instead of failing.
- Bracket citations are ambiguous outside generated drafts. Mapping `[1]` to evidence card order is explicit but should be shown as a heuristic in explanations.
- Local support scoring currently uses abstract/tag/title overlap, so it should be labeled as a support signal, not absolute truth.
