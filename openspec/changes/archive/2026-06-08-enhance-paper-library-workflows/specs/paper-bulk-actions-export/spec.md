## ADDED Requirements

### Requirement: Group report supports selectable presets
The selected-paper group-report workflow SHALL allow users to choose a report preset that shapes the generation prompt.

#### Scenario: User chooses comparison preset
- **WHEN** the user selects a cross-paper comparison preset
- **THEN** the report request includes that preset and the generated report emphasizes cross-paper comparison.

#### Scenario: User edits preset instructions
- **WHEN** the user chooses a preset and adds custom instructions
- **THEN** the backend combines the preset instructions with the custom instructions.

#### Scenario: User leaves preset as default
- **WHEN** the user generates a report with the default preset and no custom instructions
- **THEN** the existing default group-report structure is used.
