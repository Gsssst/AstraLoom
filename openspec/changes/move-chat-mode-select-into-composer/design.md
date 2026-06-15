## Context

The chat toolbar currently contains a mode select for normal conversation and Research Scout. The composer also shows a read-only mode chip, which duplicates the mental model: users see the mode near the input but must change it in the toolbar.

## Goals / Non-Goals

**Goals:**
- Let users switch assistant mode directly from the composer mode control.
- Remove the mode select from the top toolbar.
- Preserve all send-time mode behavior.

**Non-Goals:**
- Add new assistant modes.
- Change chat request payloads or backend validation.
- Redesign the full composer again.

## Decisions

1. **Use Ant Design Select inside the composer.**
   - Rationale: it preserves the existing accessible dropdown behavior and mode labels.
   - Alternative considered: custom dropdown button. Rejected because the existing Select behavior is sufficient and lower-risk.

2. **Keep a compact mode control visual.**
   - Rationale: the composer should not become crowded, especially on mobile.
   - Alternative considered: large segmented control. Rejected because the composer already has upload, runtime, and send actions.

## Risks / Trade-offs

- **Risk: Composer becomes crowded** -> Use a compact select and hide long text on mobile if needed.
- **Risk: Tests still expect toolbar mode selector** -> Update contract tests to expect the selector in the composer area.
