## Overview

The bridge turns a selected `ResearchIdea` into a `WritingProject`. It does not generate final prose through an LLM in this phase; it creates an evidence-preserving draft scaffold that users can refine with the existing writing assistant.

## Backend Design

### WritingProjectService

Add `create_review_draft_from_research_idea(user_id, research_project, idea)`.

The method:

- Extracts evidence items from `idea.evidence_json.items`.
- Resolves local paper IDs from `imported_paper_id` or UUID-shaped `paper_id`.
- Creates a `survey` writing project.
- Stores metadata:
  - `source = "research_idea"`
  - `source_project_id`
  - `source_project_name`
  - `source_idea_id`
  - `source_idea_title`
  - `recommended_paper_ids`
  - `evidence_items`
- Prefills sections:
  - Abstract: compact summary of the Proposal.
  - Introduction: problem framing from project and hypothesis.
  - Related Work: evidence papers grouped as seed/background/inspiration.
  - Related Work Comparison Table: evidence role table.
  - Research Gaps: review uncertainty, novelty, and risk framing.
  - References: local paper IDs and arXiv IDs where available.

### Research API

Add `POST /api/research/ideas/{idea_id}/writing-draft`.

The route:

- Requires the current user to own the Idea.
- Loads the owning research project.
- Calls the writing project service.
- Returns the created writing project and a short evidence summary.

## Frontend Design

### ResearchProjectPage

Each Proposal action area gets a “生成写作草稿” button. On success:

- It shows a success message.
- It navigates to `/writing?project=<writing_project_id>`.

### WritingPage

On load, the page reads `project` from URL search params. If present:

- It switches to the project tab.
- It fetches `/writing/projects/{project_id}`.
- It selects the project and loads its sections.

## Risks

- Some evidence items may still be external and not in the local paper library. The draft should preserve their title/arXiv metadata but only local paper IDs feed BibTeX export.
- If a Proposal lacks evidence, the draft should still be created but marked as evidence-insufficient.
