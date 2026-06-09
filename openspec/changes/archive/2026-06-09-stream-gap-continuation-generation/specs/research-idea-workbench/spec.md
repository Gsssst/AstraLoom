## ADDED Requirements

### Requirement: Gap Map continuation streams long-running generation
The research project workbench SHALL support streaming continuation from a reviewed Gap Map so long-running proposal generation can report progress and avoid frontend request timeout failures.

#### Scenario: Continue generation with progress events
- **WHEN** a user continues proposal generation from a selected Gap Map
- **THEN** the frontend uses a streaming continuation request and applies run, stage, artifact, done, cancelled, and error events as they arrive.

#### Scenario: Preserve synchronous compatibility
- **WHEN** an API client calls the existing non-streaming Gap Map continuation endpoint
- **THEN** the endpoint continues to return the final run response without requiring the streaming client.

#### Scenario: Cancel streaming continuation
- **WHEN** the user stops an in-progress streaming continuation
- **THEN** the frontend aborts the stream and the backend marks the run as cancelled using the existing cancellation behavior.
