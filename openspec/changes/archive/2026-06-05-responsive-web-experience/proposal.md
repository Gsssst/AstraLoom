## Why

The current web interface was built primarily for a wide desktop viewport. Shared navigation, paper search controls, paper reading, authentication cards, and the chat workspace use fixed widths or side-by-side panels that become cramped or unusable on tablets and phones.

## What Changes

- Add a responsive application shell with a mobile navigation drawer and compact content spacing.
- Make the paper library search and action controls reflow cleanly on narrow screens.
- Add a mobile reading mode for paper details so users can switch between metadata, PDF, and AI Q&A without squeezed split panes.
- Make authentication cards fit small screens with comfortable edge spacing.
- Add a compact mobile mode for the chat workspace, including a drawer-style session list and wrapped toolbar controls.
- Add reusable responsive CSS rules and keep existing desktop behavior intact.

## Capabilities

### New Capabilities
- `responsive-web-experience`: Covers adaptive navigation, narrow-screen page layout, and mobile-friendly workspace interactions.

### Modified Capabilities

None.

## Impact

- Frontend-only change.
- Affects `AppLayout`, paper library, paper detail, chat, login, and registration views.
- Adds shared responsive style rules without changing backend APIs or dependencies.
