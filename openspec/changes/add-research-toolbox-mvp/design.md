## Overview

Build the toolbox as a separate knowledge space rather than another paper-library filter. Papers remain evidence sources; toolbox entries are reusable method assets that can be selected when generating research ideas.

## Data Model

### `research_tools`

- `id`
- `name`
- `kind`: `algorithm`, `model`, `dataset`, `metric`, `framework`, `codebase`, `protocol`, `other`
- `summary`
- `use_cases`
- `limitations`
- `tags`
- `maturity`: `mature`, `experimental`, `concept`, `unknown`
- `created_by_user_id`
- timestamps

### `research_tool_papers`

- `tool_id`
- `paper_id`
- `relation`: `introduced`, `used`, `compared`, `improved`, `baseline`, `dataset`, `metric`, `other`
- `evidence_note`
- `created_by_user_id`
- timestamps

This keeps paper relationships many-to-many and allows one paper to mention several tools.

## API Shape

- `GET /api/toolbox/tools`
  - filters: `q`, `kind`, `tag`, `maturity`
- `POST /api/toolbox/tools`
- `PATCH /api/toolbox/tools/{tool_id}`
- `DELETE /api/toolbox/tools/{tool_id}`
- `POST /api/toolbox/tools/{tool_id}/papers`
- `DELETE /api/toolbox/tools/{tool_id}/papers/{paper_id}`
- `GET /api/toolbox/papers/{paper_id}/tools`

## Frontend Shape

- Add `Toolbox` to global navigation.
- Add `/toolbox` page with:
  - compact filter/search bar
  - grouped tool cards
  - create/edit drawer
  - linked paper evidence list
- Add paper page action:
  - link existing tool
  - create tool from this paper

## Research Idea Integration

Add optional selected tool IDs to idea run requests:

- `tool_ids: string[]`
- `tool_mode`: `inspiration`, `required`, `baseline`, `avoid`

The workbench loads selected tools and adds a structured `tool_context` to run config and candidate generation prompt. Generated candidates should record selected tool names or IDs when they use them.

## Boundaries

- MVP does not automatically extract tools from full text.
- MVP does not build a full graph database.
- MVP does not require every proposal to use a selected tool unless the user chooses `required`.
- MVP does not change existing paper importance markers.

## Verification

- Alembic migration creates the two tables and indexes.
- Backend tests cover CRUD, paper linking, and idea-run request persistence.
- Frontend contract tests cover navigation, toolbox page controls, and idea generation payload wiring.
- Frontend build and OpenSpec validation pass.
