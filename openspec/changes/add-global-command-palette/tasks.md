## 1. OpenSpec Validation

- [ ] 1.1 Validate the OpenSpec change before implementation.

## 2. Palette Component

- [ ] 2.1 Add a `GlobalCommandPalette` component with grouped command registry, search input, active result state, and keyboard selection.
- [ ] 2.2 Add lightweight resource search adapters that reuse existing APIs and fail softly without blocking static commands.
- [ ] 2.3 Add responsive command palette styling with stable class hooks.

## 3. App Integration

- [ ] 3.1 Replace the existing `Ctrl/⌘ + K` redirect with palette open behavior.
- [ ] 3.2 Add a visible global header trigger and update shortcut help copy.
- [ ] 3.3 Reuse route chunk prefetching for command targets where practical.

## 4. Verification

- [ ] 4.1 Add frontend contract tests for keyboard/header opening, grouped commands, resource search adapters, and no new dependency/backend endpoint.
- [ ] 4.2 Run OpenSpec strict validation after implementation.
- [ ] 4.3 Run targeted frontend contract tests.
- [ ] 4.4 Run frontend build.
- [ ] 4.5 Run `git diff --check`.
