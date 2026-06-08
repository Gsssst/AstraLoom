# paper-detail-ai-insights Specification

## Purpose
TBD - created by archiving change enhance-paper-library-workflows. Update Purpose after archive.
## Requirements
### Requirement: Paper detail exposes AI insight cards
The paper detail page SHALL provide an AI-generated insight summary for the open paper.

#### Scenario: User generates paper insights
- **WHEN** a user clicks the paper insight action on a local paper detail page
- **THEN** the backend generates and returns structured insight fields for contribution, methods, experiments, limitations, gaps, and research fit.

#### Scenario: Insight generation has cached output
- **WHEN** insight data already exists for the paper and refresh is not requested
- **THEN** the backend returns the cached insight data without calling the LLM again.

#### Scenario: Paper lacks full text
- **WHEN** a paper has no full text
- **THEN** insight generation uses title and abstract and marks evidence coverage as limited.

