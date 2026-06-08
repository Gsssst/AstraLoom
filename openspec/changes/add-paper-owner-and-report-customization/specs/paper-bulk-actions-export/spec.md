## ADDED Requirements

### Requirement: Group report prompt is customizable
The paper library SHALL let users provide custom generation instructions when creating a selected-paper group meeting report.

#### Scenario: User enters custom report instructions
- **WHEN** the user opens the group-report modal and enters custom instructions
- **THEN** report generation sends those instructions to the backend.

#### Scenario: User leaves report instructions empty
- **WHEN** the user generates a group report without custom instructions
- **THEN** the system uses the default group-report structure.

### Requirement: Group report Word export uses stable Chinese and Latin fonts
The group-report Word export SHALL use SimSun for Chinese text and Times New Roman for Latin text.

#### Scenario: User downloads a group report Word document
- **WHEN** the group report is exported as `.docx`
- **THEN** headings and body paragraphs are written with Chinese eastAsia font set to SimSun
- **AND** Latin font set to Times New Roman.
