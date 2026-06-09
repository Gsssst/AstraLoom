# bilingual-ui-switch Specification

## Purpose
Let users switch AstraLoom's shared application shell between Simplified Chinese and English at runtime while keeping the selected language locally persistent.

## Requirements

### Requirement: Users can switch UI language at runtime
The frontend SHALL let users switch the application shell between Simplified Chinese and English without a page redeploy.

#### Scenario: User chooses English
- **WHEN** a user selects English from the language switcher
- **THEN** the global navigation, header shell, shortcut modal, and settings language controls display English labels
- **AND** Ant Design built-in component locale uses English

#### Scenario: User chooses Chinese
- **WHEN** a user selects Chinese from the language switcher
- **THEN** the global navigation, header shell, shortcut modal, and settings language controls display Chinese labels
- **AND** Ant Design built-in component locale uses Chinese

### Requirement: Language preference persists locally
The frontend SHALL persist the selected language in browser local storage.

#### Scenario: User reloads the app
- **WHEN** the user changes the language and reloads the page
- **THEN** the app starts with the previously selected language

### Requirement: Translations stay structurally consistent
The i18n dictionaries SHALL keep matching translation keys for Chinese and English.

#### Scenario: Dictionary contract is tested
- **WHEN** frontend contract tests run
- **THEN** missing or extra translation keys fail the test
