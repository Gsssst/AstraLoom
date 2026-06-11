## ADDED Requirements

### Requirement: Advanced PDF parser runtime is configurable
Production deployments SHALL allow operators to configure an optional advanced PDF parser command without modifying application code, and parser subprocesses SHALL inherit configured model mirror and cache environment variables.

#### Scenario: Parser command uses HuggingFace mirror
- **WHEN** an operator configures an advanced PDF parser command that loads HuggingFace-hosted models
- **AND** `HF_ENDPOINT` is configured to a mirror endpoint
- **THEN** the parser subprocess receives `HF_ENDPOINT` and model cache environment variables
- **AND** parser model loading does not require direct connectivity to `huggingface.co`

#### Scenario: Parser command is not configured
- **WHEN** production starts without an advanced PDF parser command
- **THEN** paper PDF parsing remains available through the lightweight parser
- **AND** startup does not require Docling, MinerU, Marker, Unstructured, or other optional parser packages
