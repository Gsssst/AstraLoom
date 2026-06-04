## Why

The authenticated account entry in the application header inherits the header line height without its own alignment rules. This makes the user name appear lower than the avatar and visually detached from the account control.

## What Changes

- Add a dedicated header account chip wrapper for the avatar and visible user name.
- Normalize account chip alignment, spacing, line height, and hover feedback.
- Keep long user names contained with ellipsis and preserve the compact avatar-only mobile presentation.

## Capabilities

### New Capabilities
- `header-account-chip`: Covers the visual alignment and responsive behavior of the authenticated header account entry.

### Modified Capabilities

## Impact

- Affects the authenticated account entry in `frontend/src/components/AppLayout.tsx`.
- Adds focused responsive styles in `frontend/src/styles/responsive.css`.
- Does not change authentication data, navigation destinations, APIs, or dependencies.
