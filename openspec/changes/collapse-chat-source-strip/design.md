## Context

Research Scout now returns enough candidate references to satisfy larger requests such as ten papers. The current chat source strip renders every reference tag immediately, which can occupy several lines below a message.

LibreChat uses compact citation affordances where one visible label can represent multiple sources and details are available on interaction. Open WebUI similarly keeps citations as a separate message metadata surface rather than inline answer prose. We will adopt the same product principle in the existing Ant Design chat UI: source details remain accessible, but default reading flow stays compact.

## Decisions

1. **Use per-message local expansion state.**

   Add `expandedReferenceStrips: Set<string>` to `ChatPage`. The key should use the message id, timestamp, or index fallback, matching the existing tool trace and candidate-card expansion pattern.

2. **Keep collapsed state informative.**

   The collapsed strip shows:
   - `论文候选来源` or `检索来源`,
   - total visible reference count,
   - the first source label,
   - an expand button.

   This gives enough provenance at a glance without rendering every source tag.

3. **Render full tags only when expanded.**

   Expanded state reuses existing tooltip, click behavior, colors, and labels for each source tag, so there is no behavior regression.

4. **Style like tool trace metadata.**

   Source strips should use the same restrained border, background, compact header, and toggle shape as the collapsed tool trace component.

## Verification

- Add frontend contract tests for collapsed source strip state, toggle, summary, and expanded tag list.
- Run OpenSpec validation, the chat Research Scout contract test, and frontend build.
