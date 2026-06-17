## ADDED Requirements

### Requirement: Inline answer evidence markers bind to evidence references
The frontend SHALL bind Markdown answer markers such as `[E1]` to the structured evidence references returned with the same assistant message when the ids match.

#### Scenario: Answer text cites a returned evidence id
- **WHEN** an assistant paper-chat message contains answer text with `[E1]`
- **AND** the message references include a current-paper evidence item with id `E1`
- **THEN** the rendered marker exposes the evidence id, evidence type, and page metadata to the paper detail interaction layer.
