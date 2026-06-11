## Context

The screenshot shows a chat answer about multimodal large-language-model memory, while the displayed references are Chinese dictionary/Baidu pages for the character "请". In the current chat stream, the backend emits `references` immediately after retrieval and the frontend attaches those references to the assistant message as "引用". There is no relevance gate between fallback web results and displayed references, and the label implies the model cited each result even though the answer text may not reference them.

Admin governance currently lists workspace owner/member counts and recent activities, but direct workspace content remains available only through member-scoped `/workspaces/{space_id}`. The user explicitly wants administrator permissions widened so admins can inspect contents. This should remain explicit admin-only access rather than silently treating admins as members for ordinary workspace APIs.

Adding workspace members currently requires a typed `account` string. Existing `/admin/users` already serializes safe user profile fields. A lightweight workspace-scoped candidate endpoint can reuse that shape with membership status.

## Goals / Non-Goals

**Goals:**
- Prevent obviously unrelated web search results from becoming chat references.
- Preserve degraded operation: if filtering removes all web results, chat still answers with local context or model knowledge and clearly reports no usable web source.
- Make displayed web references easier to audit by showing the source query/provider.
- Let administrators open rich workspace content from the admin console.
- Let workspace owners choose users from a searchable list when adding members.

**Non-Goals:**
- Build full claim-level citation verification.
- Make admins mutate every workspace's content from the admin console.
- Replace workspace roles or add invitation emails.
- Add a new frontend component library.

## Decisions

- Add deterministic lexical relevance filtering in `web_search.py`.
  - Query terms are normalized across Latin words and Chinese characters.
  - Results are kept when query terms overlap title/snippet/url/query enough to be plausible.
  - Very short CJK-only query tokens such as "请" must not dominate relevance for English technical queries.
- Keep references as "retrieved sources" in the frontend.
  - Rationale: the backend cannot prove the model used each source without claim-level citation parsing.
- Add `/api/admin/workspaces/{space_id}`.
  - Rationale: it keeps privilege expansion isolated behind `require_admin` and avoids weakening member-only workspace routes.
- Extend workspace service with admin detail and member candidate helpers.
  - Rationale: serialization stays consistent with normal workspace detail and existing member/resource summaries.
- Use Ant Design `Select` with `showSearch` for member candidates.
  - Rationale: matches the existing UI stack and avoids a new dependency.

## Risks / Trade-offs

- [Risk] Lexical filtering can drop useful semantically related pages with different wording.
  -> Mitigation: keep thresholds conservative, include URL/title/snippet/query text, and retain local RAG behavior.
- [Risk] Admin detail may expose sensitive workspace resources.
  -> Mitigation: endpoint is admin-only and read-only for this change.
- [Risk] User picker could list inactive users.
  -> Mitigation: default candidate search returns active users only; typed account compatibility still respects backend user lookup.

## Verification

- Unit tests for web relevance filtering, including the observed "technical English query vs Chinese '请' dictionary pages" mismatch.
- API contract tests for admin workspace detail requiring `require_admin`.
- Service tests for member candidate rows including already-member status.
- Frontend build/type check for updated pages.
