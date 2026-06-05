# Design

## Backend

Add `WritingProjectService.build_evidence_related_work_table(project_id, user_id)`:

- Reuse `get_evidence_cards()` as the canonical evidence source.
- Build a Markdown table with title, year, evidence role, local status, identifiers, and suggested writing use.
- Return coverage metadata and warnings when local coverage is low or evidence is missing.

Expose it through:

- `POST /writing/projects/{project_id}/evidence-related-work-table`

## Frontend

The writing project page tracks the currently focused section. Evidence cards gain:

- `复制引用`
- `插入当前章节`

The evidence panel gains:

- `生成证据对比表`
- `写入对比表章节`

If no section is focused, insert actions target the first editable section and explain the fallback through a message.

## UX Rules

- Insertion appends a citation marker to the active section rather than trying to manage cursor-level edits across controlled textareas.
- Generated tables are deterministic and editable; users can still refine them.
- Warnings should be visible when cards are external-only or unavailable.

## Risks

- Appending at the end of a section is less precise than cursor insertion, but it avoids brittle textarea cursor plumbing.
- Generated tables can only be as good as the evidence metadata. The UI must label weak coverage clearly.
