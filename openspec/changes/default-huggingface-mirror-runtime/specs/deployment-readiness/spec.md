## MODIFIED Requirements

### Requirement: Runtime external resource endpoints are configurable
The deployment SHALL make external model and paper-source endpoints configurable and SHALL default HuggingFace model downloads to a mirror endpoint.

#### Scenario: HuggingFace mirror configured by default
- **WHEN** the deployment starts without an explicit `HF_ENDPOINT`
- **THEN** backend and worker model-loading environments use `https://hf-mirror.com`
- **AND** embedding and reranker model generation do not require direct connectivity to `huggingface.co`

#### Scenario: Operator overrides HuggingFace endpoint
- **WHEN** an operator sets `HF_ENDPOINT` to another HuggingFace-compatible endpoint
- **THEN** backend and worker model-loading environments use that configured endpoint
