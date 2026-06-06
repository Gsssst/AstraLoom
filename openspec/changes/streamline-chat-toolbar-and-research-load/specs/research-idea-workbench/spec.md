## ADDED Requirements

### Requirement: Research project core content is not blocked by secondary recommendations
The research project page SHALL render core workbench content after project, latest run, and experiment data are available, without waiting for related-paper recommendations.

#### Scenario: Related paper recommendation is slow
- **WHEN** the related-paper recommendation request is still pending after core project data loads
- **THEN** the page displays the project workbench and shows loading only in the related-papers panel

#### Scenario: Related paper recommendation fails
- **WHEN** the related-paper recommendation request fails
- **THEN** the project workbench remains usable and the related-papers panel falls back to an empty or non-blocking state
