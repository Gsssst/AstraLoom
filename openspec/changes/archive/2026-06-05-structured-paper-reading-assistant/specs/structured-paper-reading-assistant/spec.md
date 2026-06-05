# Capability: Structured Paper Reading Assistant

## ADDED Requirements

### Requirement: Structured Reading Templates

The paper detail page SHALL provide structured reading templates for common paper-reading tasks.

#### Scenario: User opens paper detail

- **GIVEN** the user is viewing a paper detail page
- **WHEN** the detail content panel is visible
- **THEN** the page shows an AI reading assistant section
- **AND** the section includes actions for overview, introduction, method, experiments, research gap, and meeting outline

### Requirement: Template Actions Use Existing Paper Chat

Template actions SHALL submit their prompts through the existing paper chat stream.

#### Scenario: User requests introduction reading

- **GIVEN** the user clicks the `精读 Introduction` template
- **WHEN** the template is submitted
- **THEN** a user turn appears in the paper chat
- **AND** the assistant response is generated through the same stream used by normal paper chat
- **AND** existing thinking display and reference display behavior remains available

### Requirement: Grounded Template Prompts

Template prompts SHALL instruct the model to answer based on paper content and to acknowledge missing evidence.

#### Scenario: Paper lacks requested section text

- **GIVEN** the selected paper does not provide enough Introduction content
- **WHEN** the user triggers the Introduction template
- **THEN** the prompt asks the model to clearly state that the paper content is insufficient rather than inventing details

### Requirement: Streaming Guard

The page SHALL prevent overlapping template submissions while an answer is streaming.

#### Scenario: Assistant is already answering

- **GIVEN** a paper chat response is currently streaming
- **WHEN** the user views the reading templates
- **THEN** template actions are disabled or loading
- **AND** clicking another template does not start a second overlapping answer
