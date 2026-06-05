## Overview

The writing assistant closed loop builds on the existing writing services instead of introducing a new workflow engine. The new flow is:

1. User enters a research direction.
2. Backend retrieves relevant local papers through the existing RAG service.
3. Backend creates a writing project with a survey template and prefilled sections.
4. Citation recommendation results include role labels and sentence match signals.
5. Related Work table and exports are available from the same writing/project surface.

## Backend Design

### WritingAssistantService

Add deterministic helper methods so tests and degraded environments do not depend on an LLM:

- `classify_citation_role(text, paper)`:
  - `baseline_method` when the sentence asks for baseline, comparison, benchmark, or SOTA context.
  - `counterexample` when the sentence asks about limitations, failures, negative evidence, or contradictory findings.
  - `background` when the sentence is broad survey/background framing.
  - `supporting_evidence` as the default.
- `score_sentence_paper_match(sentence, paper)`:
  - Token overlap between sentence and paper title/abstract.
  - Returns a normalized score and status: `strong`, `partial`, or `weak`.
- `generate_related_work_table(topic, max_papers)`:
  - Retrieves candidate papers and returns a Markdown table plus structured rows.

`recommend_citations` keeps its existing response fields and adds role metadata. This preserves compatibility with existing UI while giving the frontend richer display data.

### WritingProjectService

Use the existing `metadata_json` column to store draft source information:

- `source_topic`
- `recommended_paper_ids`
- `recommended_arxiv_ids`
- `related_work_table`

Add a `survey` template and a method that creates a review draft from a topic. It fills:

- Abstract
- Introduction
- Related Work
- Related Work Comparison Table
- Research Gaps
- References

Add BibTeX export for writing projects by resolving paper IDs/arXiv IDs stored in project metadata and by scanning references text as a fallback.

### API

Add endpoints:

- `POST /api/writing/projects/from-topic`
- `POST /api/writing/related-work/table`
- `POST /api/writing/citations/check-match`
- Extend `GET /api/writing/projects/{project_id}/export` to support `format=bibtex`.

## Frontend Design

The writing page receives three focused upgrades:

- Citation cards show role tags, match status, and reason.
- Related Work tab includes a comparison-table generator.
- Project tab includes a “from research direction” draft creator and BibTeX export button.

The UI remains compact; long tables and generated text reuse existing Markdown result rendering.

## Risks

- Existing RAG quality limits draft quality. The UI and metadata must show that drafts are based on local library evidence.
- Some projects may lack stored paper IDs. BibTeX export uses metadata first and section-text fallback second.
- LLM failures should not block project creation; deterministic section scaffolding provides a fallback.
