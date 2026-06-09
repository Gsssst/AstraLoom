## Overview

Use a project-local i18n implementation instead of adding a dependency. The initial scope is the application shell and shared settings controls, which are the first surfaces users see on every page. Business modules can migrate incrementally by consuming the same hook.

## Design

- Add `frontend/src/i18n/index.ts`:
  - `Language = "zh" | "en"`
  - translation dictionaries
  - `t(key, params?)` helper
  - `antdLocales` map
- Add `useLocaleStore` with:
  - persisted `language`
  - `setLanguage`
  - `t`
- `App` reads `language` and passes the matching Ant Design locale to `ConfigProvider`.
- `AppLayout` uses i18n for:
  - navigation labels
  - notification popover shell text
  - command/search trigger
  - user role labels
  - shortcut modal
  - header language switch
- `SettingsPage` adds a language card under theme settings and localizes shared theme labels.

## Boundaries

- This change does not translate all business-page content in one pass.
- API data, user content, paper metadata, and model responses remain unchanged.
- Future changes can migrate page-specific text module by module.

## Verification

- Frontend build must pass.
- Add a contract test that checks the i18n dictionary has matching keys for both languages.
- OpenSpec validation must pass.
