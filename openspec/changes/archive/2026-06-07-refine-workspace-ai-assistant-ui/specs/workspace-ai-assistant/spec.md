## MODIFIED Requirements

### Requirement: Workspace detail provides assistant UI
The frontend SHALL provide an AI assistant surface inside the project space detail page with compact context disclosure, contained references, Markdown-rendered assistant answers, quick prompts, message history, input, send state, and resource references.

#### Scenario: User opens workspace detail
- **WHEN** a project space detail page renders
- **THEN** the page includes an AI assistant panel with quick prompts, message history, input, send state, and resource references
- **AND** workspace context references are collapsed behind a compact control by default

#### Scenario: User expands assistant context
- **WHEN** a user expands the assistant context references
- **THEN** reference chips remain within the assistant card without horizontal overflow
- **AND** long reference titles are truncated with a readable label

#### Scenario: Assistant returns Markdown
- **WHEN** an assistant response contains Markdown syntax
- **THEN** the assistant message renders with the shared Markdown renderer
- **AND** user-authored messages remain compact plain text

#### Scenario: User uses a quick prompt
- **WHEN** a user activates a workspace assistant quick prompt
- **THEN** the prompt is sent through the workspace assistant flow
- **AND** the resulting answer appears in the assistant message history

#### Scenario: Assistant request fails
- **WHEN** sending a workspace assistant message fails
- **THEN** the frontend shows actionable error feedback without clearing the user's current input
