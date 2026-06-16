## Context

The app already uses `useChatAutoScroll` and disables browser scroll anchoring. The remaining issue is that streaming updates still call `scrollToBottomIfFollowing()` on every message/pending update. If the hook misses the user's upward scroll intent, `followOutputRef` stays true and every streamed chunk pulls the container back to the bottom.

The fix should live in the shared hook rather than only in `ChatPage`, because `PaperDetailPage` uses the same streaming pattern.

## Goals / Non-Goals

**Goals:**
- Treat any meaningful user movement away from the bottom as a manual pause.
- Keep pause active across streaming chunks while the user is not near the bottom.
- Resume only when the user scrolls back near the bottom or a new send calls `enableFollowOutput()`.
- Keep current behavior for users who stay at the bottom.

**Non-Goals:**
- Redesign chat layout.
- Add a visible "jump to bottom" button.
- Change backend streaming.

## Decisions

1. **Use scroll event as the source of truth.**
   - Wheel/touch/key listeners are still useful for intent, but the scroll event must pause whenever the container is not near bottom.
   - This covers trackpad inertia, scrollbar dragging, and browser/layout-driven scroll updates.

2. **Add a streaming lock.**
   - `scrollToBottomIfFollowing()` should re-check `manualPauseRef` and bottom proximity before mutating `scrollTop`.
   - When paused, streamed chunks must not scroll.

3. **Expose pause handler to containers.**
   - Pages can attach `onScroll={pauseFollowOutputIfAwayFromBottom}` so React events also call into the hook.
   - This is a defensive layer for cases where native listener timing misses a frame.

## Risks / Trade-offs

- **Users slightly above bottom may stop following** -> Keep a bottom threshold and resume automatically when they return near bottom.
- **Programmatic scroll may trigger pause** -> `enableFollowOutput()` resets the pause before sending and after manual return near bottom.
