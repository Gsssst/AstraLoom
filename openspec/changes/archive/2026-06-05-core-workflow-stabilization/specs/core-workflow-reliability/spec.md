## ADDED Requirements

### Requirement: Successful non-streaming LLM calls return generated content
The system SHALL return provider-generated text from a successful non-streaming LLM call and SHALL record token usage when usage information is available.

#### Scenario: Provider returns content on the first attempt
- **WHEN** the configured LLM provider returns a successful completion with text content
- **THEN** the service returns that text content to the caller

#### Scenario: Provider returns usage metadata
- **WHEN** the configured LLM provider returns token usage with a successful completion
- **THEN** the service invokes usage tracking before returning the generated content

### Requirement: Research Idea generation accepts selected paper provenance
The system SHALL consume selected-paper results in the `(paper, score, source)` format throughout research Idea prompt construction and SHALL preserve paper references when storing generated Ideas.

#### Scenario: Selected papers include source metadata
- **WHEN** paper selection returns candidates with paper, relevance score, and source
- **THEN** Idea generation constructs both generation prompts without tuple-unpacking errors

### Requirement: Fixed paper utility endpoints remain reachable
The system SHALL register fixed paper utility endpoints before the dynamic paper-detail endpoint.

#### Scenario: Export all papers as Markdown
- **WHEN** a client requests `GET /api/papers/export-markdown`
- **THEN** the request is handled by the Markdown export endpoint rather than parsed as a paper ID

### Requirement: Paper detail actions target valid resources
The paper detail page SHALL expose only actions backed by a valid paper-specific workflow.

#### Scenario: Paper detail toolbar is rendered
- **WHEN** a user opens a paper detail page
- **THEN** the toolbar does not offer a share action that calls a research-project endpoint with the paper ID

### Requirement: Profile update route is unique
The system SHALL register exactly one `PUT /api/settings/profile` route and SHALL preserve support for updating both email and display name.

#### Scenario: Application routes are loaded
- **WHEN** the FastAPI application registers settings routes
- **THEN** exactly one profile update route is present
