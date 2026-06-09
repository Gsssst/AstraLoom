# deployment-readiness Specification

## Purpose
Ensure production Docker deployments build reproducibly from clean image contexts without including local dependencies, build outputs, uploads, caches, or secret files.

## Requirements

### Requirement: Docker build contexts exclude local artifacts
Docker image build contexts SHALL exclude local dependency directories, build outputs, caches, uploads, and local environment files that can make server builds non-reproducible.

#### Scenario: Frontend image is built on a server with existing node_modules
- **WHEN** the frontend Docker image build context contains a local `node_modules` directory
- **THEN** Docker excludes it from the build context
- **AND** dependencies installed by `npm ci` inside the image are not overwritten by local artifacts

#### Scenario: Backend image is built on a server with runtime data
- **WHEN** the backend Docker image build context contains uploads, cache directories, virtual environments, or local env files
- **THEN** Docker excludes those artifacts from the build context
- **AND** runtime data is not baked into the backend image

### Requirement: Fresh production database migrations are complete
Fresh production deployments SHALL be able to run Alembic migrations from an empty database to the current head without missing-table failures.

#### Scenario: Workspace tables are migrated on a fresh database
- **WHEN** Alembic runs migration `022` on an empty production database after migrations `001` through `021`
- **THEN** the migration creates `project_spaces` before tables that reference it
- **AND** it creates dependent workspace membership, resource, and activity tables without missing-table failures

### Requirement: Runtime external model resources are configurable
Production Docker deployments SHALL allow operators to configure runtime model download endpoints and persistent model caches without modifying application code.

#### Scenario: Backend uses a HuggingFace mirror for embeddings
- **WHEN** the deployment sets `HF_ENDPOINT` to a HuggingFace-compatible mirror
- **AND** the backend generates paper embeddings for the first time
- **THEN** the backend model loader uses the configured endpoint through the underlying HuggingFace libraries
- **AND** embedding generation does not require direct connectivity to `huggingface.co`.

#### Scenario: Model cache survives container rebuilds
- **WHEN** the backend or worker containers are rebuilt after a model has been downloaded
- **THEN** HuggingFace and sentence-transformers cache directories remain mounted from a persistent Docker volume
- **AND** the next embedding generation can reuse cached model files.

#### Scenario: Embedding model can be pre-staged
- **WHEN** an operator sets `EMBEDDING_MODEL_NAME` to a local model path or compatible model identifier
- **THEN** the embedding service loads that configured model instead of the hard-coded default
- **AND** the default remains `all-MiniLM-L6-v2` for existing deployments.
