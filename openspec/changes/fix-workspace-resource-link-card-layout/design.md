## Context

`WorkspaceResourceLinks` is reused on paper, research project, and writing project detail pages. On the research project page it often sits inside a narrow sidebar column, where Ant Design's default `List.Item` layout gives the metadata title too little width when actions are present. Long workspace names, including English names, can then wrap one character per line.

## Goals / Non-Goals

**Goals:**
- Keep workspace names readable in narrow sidebars.
- Allow status/role tags and link/unlink buttons to wrap below the title when needed.
- Keep the existing shared component and API behavior.

**Non-Goals:**
- Redesign project-space management.
- Change workspace membership permissions.
- Add new backend fields or endpoints.

## Decisions

1. Use component-scoped classes rather than page-specific sidebar CSS.
   - Rationale: the broken card is a shared backlink component and can appear in multiple resource detail contexts.

2. Replace the fragile `List.Item` horizontal squeeze with a compact vertical row layout inside each item.
   - Rationale: narrow resource panels need predictable title width before actions; wrapping actions under the title is more readable than forcing a one-line item.

3. Use ellipsis and normal word wrapping for workspace names.
   - Rationale: long names should truncate or wrap as words where possible, not collapse into single-character columns.

## Risks / Trade-offs

- [Risk] Rows become slightly taller in narrow panels. -> Acceptable because readability and touch/click targets improve.
- [Risk] Shared component changes affect paper and writing pages. -> Scope styles to the component and preserve existing behavior.
