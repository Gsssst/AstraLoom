## ADDED Requirements

### Requirement: Generate unified diff for polished text

The system SHALL compare original text and polished text, generating a unified diff that shows additions, deletions, and unchanged sections. The diff SHALL be computed at sentence level (not character level) to provide meaningful change units. LaTeX commands, formulas, and citations SHALL be excluded from diff computation (treated as immutable blocks).

#### Scenario: Polish text and show diff

- **WHEN** user submits "The model perform good on benchmark" for academic polishing
- **THEN** the response SHALL include both the polished text and a unified diff
- **AND** the diff SHALL show "perform" → "performs" and "good" → "strong" as individual hunks

#### Scenario: LaTeX formulas unchanged in diff

- **WHEN** original text contains "$E = mc^2$"
- **AND** the text is polished
- **THEN** the diff SHALL NOT include changes to "$E = mc^2$"
- **AND** the formula SHALL appear unchanged in both original and polished versions

### Requirement: Accept or reject individual diff hunks

The system SHALL present each diff hunk as an independently actionable unit. The user SHALL be able to accept or reject each hunk individually. After processing all hunks, the system SHALL return the final text with accepted changes applied but rejected changes reverted.

#### Scenario: Accept some hunks and reject others

- **WHEN** a polish result has 5 diff hunks
- **AND** user accepts hunks 1, 2, 4 and rejects hunks 3, 5
- **THEN** the final text SHALL include changes from hunks 1, 2, 4 only
- **AND** hunks 3, 5 SHALL retain original text

#### Scenario: Accept all hunks

- **WHEN** user clicks "Accept All" on a polish result
- **THEN** all diff hunks SHALL be applied
- **AND** the final text SHALL equal the full polished version

### Requirement: Multi-round iterative polishing

The system SHALL support multiple rounds of polishing on the same text. Each round SHALL create a version record preserving the original text, polished text, and diff. The system SHALL maintain version history for up to 10 iterations per text block. The user SHALL be able to revert to any previous version.

#### Scenario: Three rounds of polishing

- **WHEN** user polishes text, then polishes the result, then polishes again
- **THEN** the system SHALL store 3 versions with incremental identifiers (v1, v2, v3)
- **AND** each version SHALL reference its parent version

#### Scenario: Revert to previous version

- **WHEN** user selects version v1 from the version history
- **THEN** the editor SHALL restore the v1 text
- **AND** versions v2 and v3 SHALL remain available in history

### Requirement: Polish style configurations

The system SHALL support four polish styles: "academic" (formal academic tone), "concise" (reduce wordiness by 20-30%), "fluent" (improve logical flow and transitions), and "english" (translate Chinese to academic English). Each style SHALL have dedicated system prompts and evaluation criteria.

#### Scenario: Academic polish

- **WHEN** style is "academic"
- **THEN** the system SHALL replace informal expressions with formal academic language
- **AND** SHALL preserve all technical terminology unchanged

#### Scenario: Chinese to English translation

- **WHEN** style is "english" and input is Chinese text
- **THEN** the system SHALL translate to academic English
- **AND** SHALL avoid Chinglish expressions
- **AND** SHALL maintain accurate technical term translations
