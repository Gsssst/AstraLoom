## ADDED Requirements

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
