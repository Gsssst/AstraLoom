# workspace-ai-assistant Specification

## Purpose
Define the project-space AI assistant that persists per-workspace conversations, grounds replies in workspace resources and activity, enforces workspace membership, and exposes the assistant in workspace detail.
## Requirements
### Requirement: Workspace exposes a scoped AI assistant
The system SHALL expose an AI assistant scoped to a single project space for authenticated workspace members.

#### Scenario: Workspace member opens assistant
- **GIVEN** a user is a member of a project space
- **WHEN** they request the workspace assistant state
- **THEN** the system returns the workspace assistant session, existing messages, quick prompts, and workspace reference summary

#### Scenario: Non-member requests assistant
- **GIVEN** a user is not a member of a project space
- **WHEN** they request or send a workspace assistant message
- **THEN** the system rejects the request

### Requirement: Workspace assistant persists per-space conversation history
The system SHALL persist assistant messages separately for each workspace so the conversation follows the project space rather than the generic chat page.

#### Scenario: User sends a workspace assistant message
- **GIVEN** a workspace member has access to a project space
- **WHEN** they send a message through the workspace assistant
- **THEN** the user message and assistant reply are persisted in a workspace-scoped assistant session
- **AND** later assistant state requests include those messages

#### Scenario: Generic chat sessions are listed
- **WHEN** a user lists generic chat sessions
- **THEN** workspace-scoped assistant sessions are not treated as ordinary chat conversations

### Requirement: Workspace assistant grounds responses in space context
The system SHALL ground workspace assistant replies in the project space's linked resources, open feedback issues, dashboard state, next actions, and recent activities.

#### Scenario: Assistant builds workspace context
- **GIVEN** a project space has linked papers, research projects, writing drafts, open feedback issues, dashboard state, and activities
- **WHEN** a user sends a workspace assistant message
- **THEN** the LLM prompt includes a concise workspace context assembled from those resources and issues
- **AND** the assistant is instructed to state when the provided context is insufficient

#### Scenario: Workspace has sparse resources
- **GIVEN** a project space has few or no linked resources
- **WHEN** a user sends a workspace assistant message
- **THEN** the assistant can still answer using dashboard, open issue, and next-action context
- **AND** the response explains which workspace resources should be added next when relevant

### Requirement: Workspace assistant returns resource references
The system SHALL return lightweight references for workspace resources and open feedback issues included in assistant context.

#### Scenario: Assistant references workspace resources
- **WHEN** a workspace assistant response uses linked papers, research projects, writing drafts, feedback issues, or activity context
- **THEN** the response includes references containing resource type, title, path, and source label

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

