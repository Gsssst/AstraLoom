## ADDED Requirements

### Requirement: Parser operations are observable
Production deployments SHALL expose structured PDF parser readiness and recent parser failures through application APIs/UI so operators can diagnose parser configuration without reading server logs first.

#### Scenario: Parser backend changes
- **WHEN** an operator enables a different structured PDF parser backend
- **THEN** admins can inspect a paper's current parser source from the application
- **AND** can rerun structured parsing to refresh cached metadata

#### Scenario: Parser backend fails
- **WHEN** the configured structured PDF parser fails for a paper
- **THEN** the latest parse failure is visible through the paper parse status
