## Overview

This change makes writing projects context-aware. A paper writing project may bind:

- a research direction project
- one or more paper collections
- target venue and year
- writing type, such as paper, survey, or grant/proposal

The project stores this binding in `metadata_json.writing_context` and uses selected collection/research papers as `recommended_paper_ids`, so existing evidence cards, BibTeX export, citation checks, and workbench summary continue to work.

## Backend

### Request Model

`ProjectCreateRequest` accepts optional context fields:

- `writing_type`
- `research_project_id`
- `collection_ids`
- `target_venue`
- `target_year`

### Context Resolution

`WritingProjectService.create_project_from_context` resolves:

- owned research project metadata and seed `paper_ids`
- owned folder names and folder paper IDs
- deduplicated local paper IDs

If an ID is invalid or inaccessible, the API returns a clear validation error.

### Seed Draft Sections

After creating the project, the service pre-fills key sections when they exist:

- Introduction: topic, target venue, context description
- Related Work: initial evidence summary
- Related Work Comparison Table: structured table from local evidence cards
- References: local Paper IDs and identifiers

This is deterministic scaffolding, not final AI prose.

## Frontend

`WritingProjectPanel` loads:

- `/research/projects`
- `/folders/`

The create modal exposes:

- writing type
- structure template
- target venue/year
- research direction selector
- paper collection multi-select

The selected project card and workbench summary can show context chips through project metadata.

## Tradeoffs

- The first version binds research projects at the project level, but does not yet import a specific idea's experiment plan unless created through the existing research-idea draft flow.
- Context-based prefill is intentionally conservative so users do not mistake it for a finished paper section.
