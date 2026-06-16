## Context

Tool traces are now shown for Research Scout agent runs. The full step list is valuable, but it competes with the answer and candidate cards for vertical space.

## Goals / Non-Goals

**Goals:**
- Collapse tool traces by default.
- Keep a compact, scannable summary visible.
- Let users expand a trace in place without losing existing card actions or message content.

**Non-Goals:**
- Changing backend trace payloads.
- Persisting per-message expanded state across reloads.

## Decisions

- Track expanded trace message keys in local React state, similar to expanded Research Scout candidate cards.
- Render the trace header and summary always; render step details only when expanded.
- Use a small text button with an icon to toggle details so the collapsed trace remains compact.

## Risks / Trade-offs

- **Users may miss hidden details** -> Keep step count and latest status visible in the collapsed header.
- **Streaming messages may not have stable IDs** -> Use the same fallback key pattern already used for Research Scout cards.
