## ADDED Requirements

### Requirement: Chat toolbar avoids crowded primary rows
The chat toolbar SHALL keep detailed model capability status and low-frequency conversation actions out of the main row while preserving access to them through compact controls.

#### Scenario: View chat toolbar on desktop
- **WHEN** a user opens the chat workspace on a desktop viewport
- **THEN** the primary toolbar shows the conversation title and compact chat controls without repeating status badges across the full width

#### Scenario: Inspect model capabilities
- **WHEN** a user needs model or capability details
- **THEN** the toolbar provides a compact status affordance that exposes model, knowledge-base, web, thinking, and vision state

#### Scenario: Use secondary chat actions
- **WHEN** a user needs search, export, or clear-conversation actions
- **THEN** those actions remain reachable without dominating the primary toolbar
