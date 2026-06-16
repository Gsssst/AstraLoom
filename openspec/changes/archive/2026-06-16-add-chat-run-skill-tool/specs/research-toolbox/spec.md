## ADDED Requirements

### Requirement: Built-in research skills are inspectable toolbox assets
The system SHALL expose built-in research skills as structured toolbox assets that can be called by chat through the shared tool runtime.

#### Scenario: List built-in research skills
- **WHEN** backend code asks for built-in research skills
- **THEN** it receives stable skill definitions containing id, label, description, allowed tool hints, output format, and evaluation criteria

#### Scenario: Built-in skills cover core research workflows
- **WHEN** the built-in registry is initialized
- **THEN** it includes skills for paper scouting, method comparison, experiment planning, survey drafting, figure interpretation, and rebuttal help

#### Scenario: Skill definitions remain declarative
- **WHEN** a built-in skill is loaded
- **THEN** the definition is data-only guidance
- **AND** it does not execute arbitrary code or bypass chat tool validation
