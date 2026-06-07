## Why

Major pages currently define their own outer widths, hero/header treatment, spacing, and content containers. This makes the app feel uneven and increases the chance that future UI improvements repeat layout code.

## What Changes

- Add a reusable frontend `PageShell` component for standard page title, subtitle, actions, max-width, and content spacing.
- Add shared CSS class hooks for the page shell so future pages can adopt the same layout contract.
- Adopt the shell in the Settings page as the first low-risk page.
- Keep existing application layout, navigation, settings tabs, data fetching, and business logic unchanged.

## Capabilities

### New Capabilities

### Modified Capabilities
- `shared-layout-boundaries`: Pages should be able to opt into a shared page shell for consistent title/action/content spacing inside the existing app layout.

## Impact

- `frontend/src/components/PageShell.tsx`
- `frontend/src/styles/page-shell.css`
- `frontend/src/pages/SettingsPage.tsx`
- Frontend layout contract tests.
- No backend API, database, or dependency changes.
