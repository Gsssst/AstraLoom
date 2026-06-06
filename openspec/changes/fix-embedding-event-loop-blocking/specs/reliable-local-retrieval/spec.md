## ADDED Requirements

### Requirement: Local embedding work does not block unrelated API handling
The system SHALL run synchronous local embedding model loading and text encoding outside the main asyncio event loop.

#### Scenario: Cold embedding model loads during retrieval
- **WHEN** dense or hybrid retrieval triggers the first local embedding model load
- **THEN** unrelated async endpoints remain able to run while the model is loading

#### Scenario: Concurrent embedding requests share initialization
- **WHEN** multiple embedding requests start while no local embedding model is loaded
- **THEN** the system initializes one process-local model instance and reuses it for those requests
