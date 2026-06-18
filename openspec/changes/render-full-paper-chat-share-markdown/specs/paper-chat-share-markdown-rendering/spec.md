## ADDED Requirements

### Requirement: Shared paper chat messages render as Markdown
The paper push center SHALL render paper chat share message bodies with Markdown and LaTeX support.

#### Scenario: Shared answer contains Markdown or formula syntax
- **GIVEN** a paper chat share message includes Markdown, code, table, or LaTeX syntax in `content`
- **WHEN** the recipient views the share in the paper push center
- **THEN** the message body is rendered through the app Markdown renderer

#### Scenario: Shared answer has both content and excerpt
- **GIVEN** a shared message contains both `content` and `excerpt`
- **WHEN** the paper push center renders the message
- **THEN** the full `content` is preferred over the shorter `excerpt`
