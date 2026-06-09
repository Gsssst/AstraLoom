## Why

AstraLoom currently presents the UI mostly in Chinese and has no runtime language preference. Bilingual teams need a way to switch between Chinese and English without redeploying the app, starting with the global shell and shared UI surfaces.

## What Changes

- Add a lightweight frontend i18n layer with Chinese and English dictionaries.
- Persist the selected language in local storage.
- Switch Ant Design locale between Chinese and English.
- Add language switch controls in the global header and settings page.
- Migrate global shell text, navigation labels, shortcut modal, notifications shell, route loading state, and settings theme labels to the i18n layer.

## Capabilities

### New Capabilities
- `bilingual-ui-switch`: Users can switch the application shell between Chinese and English at runtime.

### Modified Capabilities

## Impact

- Frontend stores and shared i18n utilities.
- `App`, `AppLayout`, and `SettingsPage`.
- Frontend build and contract tests.
